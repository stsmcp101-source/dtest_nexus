import os
import re

import openpyxl
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.permissions.decorators import require_permission

from .forms import DocumentForm, EquipmentSpecForm, EquipmentSpecImportForm
from .models import Document, DocumentCategory, DocumentSource, EquipmentSpec
from .selectors import get_category_counts, get_document_queryset, get_equipment_spec_queryset, get_year_counts
from .spec_import import SpecImportError, import_equipment_specs_from_excel
from .storage import (
    UnsupportedProviderError, detect_category_code, detect_document_year,
    get_download_url, get_open_url, validate_upload,
)


def _unique_document_code(stem):
    """Turns a filename stem into a document_code, disambiguating against
    any existing code by appending -2, -3, ... instead of failing."""
    base = re.sub(r"[^A-Za-z0-9\-_]+", "-", stem).strip("-").upper() or "DOC"
    code = base
    suffix = 2
    while Document.objects.filter(document_code=code).exists():
        code = f"{base}-{suffix}"
        suffix += 1
    return code


def _create_documents_from_files(request, files, description, year_override=None):
    local_source = DocumentSource.objects.filter(
        provider_type=DocumentSource.ProviderType.LOCAL, is_active=True
    ).first()
    created = []
    for f in files:
        try:
            validate_upload(
                f, getattr(settings, "DOCUMENTS_ALLOWED_EXTENSIONS", []),
                getattr(settings, "DOCUMENTS_MAX_UPLOAD_SIZE_MB", 25),
            )
        except ValidationError as exc:
            messages.error(request, f"{f.name}: {'; '.join(exc.messages)}")
            continue

        stem = os.path.splitext(f.name)[0].strip()
        category = DocumentCategory.objects.get(code=detect_category_code(f.name))
        document = Document.objects.create(
            document_code=_unique_document_code(stem),
            document_name=stem,
            category=category,
            document_year=detect_document_year(f.name) or year_override,
            source=local_source,
            file=f,
            description=description,
            status=Document.Status.ACTIVE,
            created_by=request.user,
            updated_by=request.user,
        )
        log_action(
            user=request.user, action="UPLOAD", module="documents",
            object_type="Document", object_id=document.pk,
            description=f"Uploaded document '{document.document_code}'.",
            ip_address=get_client_ip(request),
        )
        created.append(document)
    return created


# NOTE: document_list / document_detail / document_open are intentionally
# PUBLIC (no @login_required, no @require_permission) — Document Data is a
# view-anywhere module per the business requirement "หน้า Document Data
# เข้าดูได้เลย ไม่ต้องเข้าระบบ". Upload/Edit/Delete/Download remain
# permission-gated below, and since apps.permissions.registry.user_has()
# returns False for any unauthenticated user, those actions stay fully
# protected for anonymous visitors even without an explicit login_required.
def document_list(request):
    category_code = request.GET.get("category", "all")
    search = request.GET.get("q", "").strip()
    file_type = request.GET.get("file_type", "").strip()
    sort = request.GET.get("sort", "recent")

    documents = get_document_queryset(
        category_code=category_code, search=search, file_type=file_type, sort=sort
    )

    paginator = Paginator(documents, getattr(settings, "DEFAULT_PAGE_SIZE", 10))
    page_obj = paginator.get_page(request.GET.get("page"))

    year_counts, max_year_count = get_year_counts(category_code)

    context = {
        "page_obj": page_obj,
        "category_counts": get_category_counts(),
        "selected_category": category_code,
        "q": search,
        "file_type": file_type,
        "sort": sort,
        "total_count": Document.objects.count(),
        "year_counts": year_counts,
        "max_year_count": max_year_count,
    }
    return render(request, "documents/document_list.html", context)


def equipment_spec_list(request):
    """
    Public spec-sheet list — No / Year / Indoor / Outdoor / Report Dev /
    Report Sam — matching the spreadsheet layout the business already
    keeps this data in. Viewing (and searching) is open to everyone,
    same as the rest of Document Data; adding a row (one at a time or
    via Excel import) and editing/deleting rows are gated below.
    """
    search = request.GET.get("q", "").strip()
    specs = get_equipment_spec_queryset(search=search)
    page_obj = Paginator(specs, getattr(settings, "DEFAULT_PAGE_SIZE", 20)).get_page(request.GET.get("page"))

    codes = set()
    for spec in page_obj:
        codes.update(filter(None, [spec.report_dev_code, spec.report_sam_code]))
    documents_by_code = {
        doc.document_code: doc.pk for doc in Document.objects.filter(document_code__in=codes)
    }

    context = {
        "page_obj": page_obj,
        "documents_by_code": documents_by_code,
        "import_form": EquipmentSpecImportForm(),
        "q": search,
    }

    if request.GET.get("partial") == "rows":
        pagination_qs = request.GET.copy()
        pagination_qs.pop("partial", None)
        pagination_qs.pop("page", None)
        rows_html = render_to_string("documents/_equipment_spec_rows.html", context, request=request)
        pagination_html = render_to_string(
            "components/pagination.html",
            {"page_obj": page_obj, "querystring": pagination_qs.urlencode()},
            request=request,
        )
        return JsonResponse({
            "rows_html": rows_html,
            "pagination_html": pagination_html,
            "count": page_obj.paginator.count,
        })

    return render(request, "documents/equipment_spec_list.html", context)


def equipment_spec_export(request):
    """Exports the (optionally search-filtered) spec list as .xlsx, using
    the same column layout the import expects — so a user can export,
    edit in Excel, and re-import."""
    search = request.GET.get("q", "").strip()
    specs = get_equipment_spec_queryset(search=search)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Equipment Specs"
    sheet.append(["No", "Year", "Indoor", "Outdoor", "Report Dev", "Report Sam"])
    for i, spec in enumerate(specs, start=1):
        sheet.append([i, spec.year, spec.indoor_unit, spec.outdoor_unit, spec.report_dev_code, spec.report_sam_code])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="equipment_specs.xlsx"'
    workbook.save(response)
    return response


@login_required
@require_permission("document.upload")
def equipment_spec_create(request):
    if request.method == "POST":
        form = EquipmentSpecForm(request.POST)
        if form.is_valid():
            spec = form.save(commit=False)
            spec.created_by = request.user
            spec.updated_by = request.user
            spec.save()
            messages.success(request, "เพิ่มรายการสเปคเรียบร้อยแล้ว")
            return redirect("documents:spec_list")
    else:
        form = EquipmentSpecForm()
    return render(request, "documents/equipment_spec_form.html", {"form": form, "mode": "create"})


@login_required
@require_permission("document.edit")
def equipment_spec_edit(request, pk):
    spec = get_object_or_404(EquipmentSpec, pk=pk)
    if request.method == "POST":
        form = EquipmentSpecForm(request.POST, instance=spec)
        if form.is_valid():
            spec = form.save(commit=False)
            spec.updated_by = request.user
            spec.save()
            messages.success(request, "บันทึกรายการสเปคแล้ว")
            return redirect("documents:spec_list")
    else:
        form = EquipmentSpecForm(instance=spec)
    return render(request, "documents/equipment_spec_form.html", {"form": form, "mode": "edit", "spec": spec})


@login_required
@require_permission("document.delete")
def equipment_spec_delete(request, pk):
    spec = get_object_or_404(EquipmentSpec, pk=pk)
    if request.method == "POST":
        spec.delete()
        messages.success(request, "ลบรายการสเปคแล้ว")
        return redirect("documents:spec_list")
    return render(request, "documents/equipment_spec_confirm_delete.html", {"spec": spec})


@login_required
@require_permission("document.upload")
def equipment_spec_import(request):
    if request.method == "POST":
        form = EquipmentSpecImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                created, errors = import_equipment_specs_from_excel(request.FILES["excel_file"], request.user)
            except SpecImportError as exc:
                messages.error(request, str(exc))
            else:
                if created:
                    messages.success(request, f"นำเข้าข้อมูลสำเร็จ {created} แถว")
                if errors:
                    preview = "; ".join(f"แถว {n}: {msg}" for n, msg in errors[:5])
                    messages.warning(request, f"ข้าม {len(errors)} แถวที่มีปัญหา — {preview}")
                if not created and not errors:
                    messages.warning(request, "ไม่พบข้อมูลที่นำเข้าได้ในไฟล์นี้")
        else:
            messages.error(request, "กรุณาเลือกไฟล์ Excel (.xlsx)")
    return redirect("documents:spec_list")


def document_search_suggest(request):
    """
    Powers the live search-as-you-type dropdown on the search box (public,
    same as document_list — it only ever returns what an anonymous visitor
    could already see via the regular list/search). Returns a small JSON
    payload; the highlighting itself happens client-side so this stays a
    plain data endpoint.
    """
    search = request.GET.get("q", "").strip()
    if not search:
        return JsonResponse({"results": []})

    documents = get_document_queryset(search=search)[:8]
    results = [
        {
            "id": doc.pk,
            "document_code": doc.document_code,
            "document_name": doc.document_name,
            "category_name": doc.category.name,
            "url": reverse("documents:detail", args=[doc.pk]),
        }
        for doc in documents
    ]
    return JsonResponse({"results": results})


def document_detail(request, pk):
    document = get_object_or_404(Document.objects.select_related("category", "document_type", "source"), pk=pk)
    log_action(
        user=request.user, action="VIEW", module="documents",
        object_type="Document", object_id=document.pk, description=f"Viewed '{document.document_code}'.",
        ip_address=get_client_ip(request),
    )
    return render(request, "documents/document_detail.html", {"document": document})


@login_required
@require_permission("document.upload")
def document_create(request):
    """
    Primary path: drag-and-drop / multi-select local files, one Document
    per file, with document_code/document_name/category all derived from
    each filename automatically (rule requested by the business — files
    are only ever named with SAM or DEV, so there is nothing left for the
    uploader to fill in beyond the shared, optional business unit /
    description). A secondary "link_form" (collapsed in the template)
    still covers the less common external-source case (Google Drive,
    SharePoint, network drive, or a bare URL), where there is no local
    file to name the document from.
    """
    if request.method == "POST" and request.FILES.getlist("files"):
        files = request.FILES.getlist("files")
        year_raw = request.POST.get("document_year", "").strip()
        created = _create_documents_from_files(
            request, files,
            description=request.POST.get("description", "").strip(),
            year_override=int(year_raw) if year_raw.isdigit() else None,
        )
        if created:
            messages.success(request, f"อัปโหลดเอกสารสำเร็จ {len(created)} ไฟล์")
            if len(created) == 1:
                return redirect("documents:detail", pk=created[0].pk)
            return redirect("documents:list")
        messages.error(request, "ไม่มีไฟล์ที่อัปโหลดสำเร็จ กรุณาลองใหม่อีกครั้ง")

    elif request.method == "POST" and request.POST.get("link_mode"):
        link_form = DocumentForm(request.POST, request.FILES)
        if link_form.is_valid():
            document = link_form.save(commit=False)
            document.category = DocumentCategory.objects.get(
                code=detect_category_code(document.document_name or document.document_code)
            )
            if not document.document_year:
                document.document_year = detect_document_year(document.document_code) or detect_document_year(
                    document.document_name
                )
            document.created_by = request.user
            document.updated_by = request.user
            document.save()
            log_action(
                user=request.user, action="UPLOAD", module="documents",
                object_type="Document", object_id=document.pk,
                description=f"Uploaded document '{document.document_code}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"เพิ่มเอกสาร '{document.document_code}' เรียบร้อยแล้ว")
            return redirect("documents:detail", pk=document.pk)
        return render(request, "documents/document_form.html", {"link_form": link_form, "mode": "create"})

    link_form = DocumentForm(initial={
        "source": DocumentSource.objects.exclude(provider_type=DocumentSource.ProviderType.LOCAL)
        .filter(is_active=True).first()
    })
    return render(request, "documents/document_form.html", {"link_form": link_form, "mode": "create"})


@login_required
@require_permission("document.edit")
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.updated_by = request.user
            document.save()
            log_action(
                user=request.user, action="UPDATE", module="documents",
                object_type="Document", object_id=document.pk,
                description=f"Updated document '{document.document_code}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"บันทึกเอกสาร '{document.document_code}' แล้ว")
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentForm(instance=document)
    return render(request, "documents/document_form.html", {"form": form, "mode": "edit", "document": document})


@login_required
@require_permission("document.delete")
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == "POST":
        code = document.document_code
        document.delete()
        log_action(
            user=request.user, action="DELETE", module="documents",
            object_type="Document", object_id=pk, description=f"Deleted document '{code}'.",
            ip_address=get_client_ip(request),
        )
        messages.success(request, f"ลบเอกสาร '{code}' แล้ว")
        return redirect("documents:list")
    return render(request, "documents/document_confirm_delete.html", {"document": document})


def document_open(request, pk):
    """
    Redirects to wherever this document's bytes actually live (local
    media URL, or an external Drive/SharePoint/URL reference) via the
    storage abstraction — the view never assumes a provider. Public,
    same as document_list / document_detail.
    """
    document = get_object_or_404(Document, pk=pk)
    try:
        url = get_open_url(document)
    except UnsupportedProviderError as exc:
        messages.error(request, str(exc))
        return redirect("documents:detail", pk=pk)

    log_action(
        user=request.user, action="VIEW", module="documents",
        object_type="Document", object_id=document.pk, description=f"Opened '{document.document_code}'.",
        ip_address=get_client_ip(request),
    )
    return redirect(url)


@login_required
@require_permission("document.download")
def document_download(request, pk):
    document = get_object_or_404(Document, pk=pk)

    log_action(
        user=request.user, action="DOWNLOAD", module="documents",
        object_type="Document", object_id=document.pk, description=f"Downloaded '{document.document_code}'.",
        ip_address=get_client_ip(request),
    )

    if document.source.provider_type == DocumentSource.ProviderType.LOCAL:
        if not document.file:
            raise Http404("ไม่พบไฟล์เอกสารนี้")
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.display_filename)

    try:
        url = get_download_url(document)
    except UnsupportedProviderError as exc:
        messages.error(request, str(exc))
        return redirect("documents:detail", pk=pk)
    return redirect(url)
