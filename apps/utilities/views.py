from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.core.models import SystemSettings
from apps.permissions.decorators import require_permission

from . import converters, pdf_tools, qr_tools
from .forms import ToolIconSettingsForm, ToolLinkSettingsForm
from .icon_memory import remember_icon, tool_icon_urls
from .models import ToolIcon
from .pdf_tools import ToolError
from .tool_icons import TOOL_ICONS


# NOTE: Tools (the hub page below and every sub-tool: PDF Edit, QR Code,
# Document Converter, Calculators, Engineering) is intentionally PUBLIC —
# no @login_required, no @require_permission — same rationale as
# apps.documents' public list/detail/download views: it's a view-anywhere
# module. link_settings below stays permission-gated since editing the
# external system links is an administrative action, not "using a tool".
def index(request):
    context = {
        "module_title": "Tools",
        "module_tag": "MODULE 06 — TOOL",
        "module_description": "เครื่องมือช่วยงานประจำวัน เช่น แบบฟอร์มกลางและตัวช่วยคำนวณ",
        "system_settings": SystemSettings.get_solo(),
        "tool_icon_urls": _tool_icon_urls(),
    }
    return render(request, "utilities/index.html", context)


def _tool_icon_urls():
    return tool_icon_urls()


@login_required
@require_permission("settings.edit")
def icon_settings(request):
    if request.method == "POST":
        form = ToolIconSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            existing = {icon.key: icon for icon in ToolIcon.objects.all()}
            changed = []
            for key, _section, name, _svg in TOOL_ICONS:
                upload = form.cleaned_data[f"icon_{key}"]
                icon = existing.get(key)
                if upload:
                    if not icon:
                        icon = ToolIcon(key=key)
                    icon.image = upload
                    icon.save()
                    changed.append(f"{name}: โลโก้ใหม่")
                elif form.cleaned_data[f"reset_{key}"]:
                    if icon:
                        icon.delete()
                    else:
                        remember_icon(key, None)
                    changed.append(f"{name}: กลับเป็นไอคอนเดิม")
            if changed:
                log_action(
                    user=request.user, action="UPDATE", module="utilities", object_type="ToolIcon",
                    description="อัปเดตโลโก้หน้า Tools — " + ", ".join(changed),
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "บันทึกโลโก้เรียบร้อยแล้ว")
            else:
                messages.info(request, "ไม่มีการเปลี่ยนแปลงโลโก้")
            return redirect("utilities:index")
    else:
        form = ToolIconSettingsForm()

    icon_urls = _tool_icon_urls()
    sections = {}
    for key, section, name, _svg in TOOL_ICONS:
        sections.setdefault(section, []).append({
            "key": key, "name": name, "has_custom": key in icon_urls,
            "upload": form[f"icon_{key}"], "reset": form[f"reset_{key}"],
        })
    return render(request, "utilities/icon_settings.html", {
        "form": form, "sections": sections, "tool_icon_urls": icon_urls,
    })


@login_required
@require_permission("settings.edit")
def link_settings(request):
    settings_obj = SystemSettings.get_solo()
    if request.method == "POST":
        form = ToolLinkSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user, action="UPDATE", module="utilities", object_type="SystemSettings",
                description="อัปเดตลิงก์ระบบภายนอกของหน้า Tools (Approve Doc / KACE / PScapa)",
                ip_address=get_client_ip(request),
            )
            messages.success(request, "บันทึกลิงก์เรียบร้อยแล้ว")
            return redirect("utilities:index")
    else:
        form = ToolLinkSettingsForm(instance=settings_obj)
    return render(request, "utilities/link_settings.html", {"form": form})


# ---------------------------------------------------------------------------
# PDF Edit
# ---------------------------------------------------------------------------

def pdf_edit(request):
    return render(request, "utilities/pdf_edit.html", {"tool_icon_urls": _tool_icon_urls()})


def _pdf_response(buffer, filename, content_type="application/pdf"):
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type=content_type)


def _json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


# All PDF Edit sub-tools below are called exclusively via fetch/XHR from
# tools_pdf_edit.js (ordered file lists, live page pickers, and an upload
# progress bar all need that — a classic multipart form post can't drive
# them), so errors come back as JSON instead of Django messages + redirect.

def pdf_page_count(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    f = request.FILES.get("file")
    if not f:
        return _json_error("กรุณาเลือกไฟล์ PDF")
    try:
        pages = pdf_tools.get_page_count(f)
    except ToolError as exc:
        return _json_error(str(exc))
    return JsonResponse({"pages": pages})


def pdf_merge(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    files = request.FILES.getlist("files")
    try:
        result = pdf_tools.merge_pdfs(files)
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"PDF Edit: รวมไฟล์ {len(files)} ไฟล์ -> merged.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "merged.pdf")


def pdf_split(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    f = request.FILES.get("file")
    if not f:
        return _json_error("กรุณาเลือกไฟล์ PDF")

    mode = request.POST.get("mode", "all")
    ranges = request.POST.get("ranges", "").strip()
    pages = request.POST.get("pages", "").strip()

    try:
        if ranges:
            # Manual entry always overrides mouse selection / mode.
            result = pdf_tools.split_pdf(f, ranges_spec=ranges)
            filename, content_type = "split.zip", "application/zip"
        elif mode == "selected_each":
            if not pages:
                return _json_error("กรุณาเลือกหน้าที่ต้องการอย่างน้อย 1 หน้า")
            result = pdf_tools.split_pdf(f, ranges_spec=pages)
            filename, content_type = "split.zip", "application/zip"
        elif mode == "selected_combined":
            if not pages:
                return _json_error("กรุณาเลือกหน้าที่ต้องการอย่างน้อย 1 หน้า")
            result = pdf_tools.extract_pages(f, pages)
            filename, content_type = "extracted.pdf", "application/pdf"
        elif mode == "chunks":
            chunk_raw = request.POST.get("chunk_size", "").strip()
            if not chunk_raw.isdigit():
                return _json_error("จำนวนหน้าต่อไฟล์ต้องเป็นตัวเลข")
            result = pdf_tools.split_pdf(f, chunk_size=int(chunk_raw))
            filename, content_type = "split.zip", "application/zip"
        else:
            result = pdf_tools.split_pdf(f)
            filename, content_type = "split.zip", "application/zip"
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"PDF Edit: แยกไฟล์ '{f.name}' -> {filename}",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, filename, content_type=content_type)


def pdf_delete_pages(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    f = request.FILES.get("file")
    if not f:
        return _json_error("กรุณาเลือกไฟล์ PDF")
    try:
        result = pdf_tools.delete_pages(f, request.POST.get("pages", ""))
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"PDF Edit: ลบหน้าออกจาก '{f.name}' -> deleted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "deleted.pdf")


def pdf_insert(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    base_file = request.FILES.get("base_file")
    insert_files = request.FILES.getlist("insert_files")
    mode = request.POST.get("mode", "end")
    position_raw = request.POST.get("position", "0").strip()
    if not base_file or not insert_files:
        return _json_error("กรุณาเลือกไฟล์หลักและไฟล์ที่จะแทรกให้ครบ")
    if mode == "custom" and not position_raw.isdigit():
        return _json_error("ตำแหน่งแทรกต้องเป็นตัวเลข")

    try:
        result = pdf_tools.insert_pdf(
            base_file, insert_files, mode=mode, custom_position=int(position_raw or 0)
        )
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"PDF Edit: แทรกไฟล์ {len(insert_files)} ไฟล์เข้าไปใน '{base_file.name}' -> inserted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "inserted.pdf")


def pdf_encrypt(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    f = request.FILES.get("file")
    password = request.POST.get("password", "")
    owner_password = request.POST.get("owner_password", "")
    if not f:
        return _json_error("กรุณาเลือกไฟล์ PDF")
    try:
        result = pdf_tools.encrypt_pdf(f, password, owner_password=owner_password)
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPDATE", module="utilities", object_type="PDF",
        description=f"PDF Edit: ล็อกไฟล์ '{f.name}' ด้วยรหัสผ่าน -> encrypted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "encrypted.pdf")


def pdf_decrypt(request):
    if request.method != "POST":
        return _json_error("Method not allowed", status=405)
    f = request.FILES.get("file")
    password = request.POST.get("password", "")
    if not f:
        return _json_error("กรุณาเลือกไฟล์ PDF")
    try:
        result = pdf_tools.decrypt_pdf(f, password)
    except ToolError as exc:
        return _json_error(str(exc))

    log_action(
        user=request.user, action="UPDATE", module="utilities", object_type="PDF",
        description=f"PDF Edit: ปลดล็อกไฟล์ '{f.name}' -> decrypted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "decrypted.pdf")


# ---------------------------------------------------------------------------
# QR Code
# ---------------------------------------------------------------------------

def qr_code_page(request):
    return render(request, "utilities/qr_code.html", {"tool_icon_urls": _tool_icon_urls()})


def qr_generate(request):
    data = request.GET.get("data", "").strip()
    fmt = request.GET.get("format", "png").strip().lower()
    try:
        image = qr_tools.build_image(
            data,
            fg_color=request.GET.get("fg", "#000000"),
            bg_color=request.GET.get("bg", "#ffffff"),
            shape=request.GET.get("shape", "square"),
        )
    except ToolError as exc:
        return HttpResponseBadRequest(str(exc))

    buffer, content_type = qr_tools.image_to_bytes(image, fmt=fmt)
    filename = "qrcode.jpg" if fmt == "jpg" else "qrcode.png"

    if request.GET.get("download"):
        log_action(
            user=request.user, action="CREATE", module="utilities", object_type="QRCode",
            description="สร้าง QR Code และดาวน์โหลด",
            ip_address=get_client_ip(request),
        )
        return FileResponse(buffer, as_attachment=True, filename=filename, content_type=content_type)
    return HttpResponse(buffer.getvalue(), content_type=content_type)


# ---------------------------------------------------------------------------
# Document Converter
# ---------------------------------------------------------------------------

def document_converter(request):
    return render(request, "utilities/document_converter.html", {"tool_icon_urls": _tool_icon_urls()})


def convert_images_to_pdf(request):
    if request.method != "POST":
        return redirect("utilities:document_converter")
    files = request.FILES.getlist("files")
    try:
        result = converters.images_to_pdf(files)
    except ToolError as exc:
        messages.error(request, str(exc))
        return redirect("utilities:document_converter")

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"Document Converter: แปลงรูปภาพ {len(files)} ไฟล์ -> converted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "converted.pdf")


def convert_pdf_to_images(request):
    if request.method != "POST":
        return redirect("utilities:document_converter")
    f = request.FILES.get("file")
    if not f:
        messages.error(request, "กรุณาเลือกไฟล์ PDF")
        return redirect("utilities:document_converter")
    try:
        result = converters.pdf_to_images(f)
    except ToolError as exc:
        messages.error(request, str(exc))
        return redirect("utilities:document_converter")

    log_action(
        user=request.user, action="DOWNLOAD", module="utilities", object_type="PDF",
        description=f"Document Converter: แปลง '{f.name}' เป็นรูปภาพ -> pages.zip",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "pages.zip", content_type="application/zip")


def convert_office_to_pdf(request):
    if request.method != "POST":
        return redirect("utilities:document_converter")
    f = request.FILES.get("file")
    if not f:
        messages.error(request, "กรุณาเลือกไฟล์ Word หรือ Excel")
        return redirect("utilities:document_converter")
    try:
        result = converters.office_to_pdf(f)
    except ToolError as exc:
        messages.error(request, str(exc))
        return redirect("utilities:document_converter")

    log_action(
        user=request.user, action="UPLOAD", module="utilities", object_type="PDF",
        description=f"Document Converter: แปลง '{f.name}' เป็น PDF -> converted.pdf",
        ip_address=get_client_ip(request),
    )
    return _pdf_response(result, "converted.pdf")


# ---------------------------------------------------------------------------
# Calculators / Engineering — pure client-side pages, view just renders.
# ---------------------------------------------------------------------------

# Each calculator is its own page (like PDF Edit / QR Code); its form lives in
# templates/utilities/calc/<key>.html. key: (group, title, description)
CALC_TOOLS = {
    "temperature": ("calculators", "Temperature", "แปลงหน่วยอุณหภูมิ °C / °F / K"),
    "capacity": ("calculators", "Capacity", "แปลงหน่วยความเย็น BTU/hr, TR, kW, kcal/hr"),
    "salary": ("calculators", "Salary", "คำนวณเงินเดือน รายวัน รายชั่วโมง และค่าล่วงเวลา"),
    "unit": ("calculators", "Unit Converter", "แปลงหน่วยความยาว น้ำหนัก ปริมาตร และพื้นที่"),
    "percentage": ("calculators", "Percentage", "คำนวณเปอร์เซ็นต์ ส่วนลด และอัตราการเปลี่ยนแปลง"),
    "datetime": ("calculators", "Date & Time", "คำนวณระยะห่างวันที่ และบวก/ลบวัน"),
    "oee": ("engineering", "OEE", "Overall Equipment Effectiveness — Availability × Performance × Quality"),
    "cycle": ("engineering", "Cycle Time", "เวลาที่ใช้จริงในการผลิตต่อชิ้น"),
    "power": ("engineering", "Power", "คำนวณกำลังไฟฟ้า 1 เฟส และ 3 เฟส"),
    "pressure": ("engineering", "Pressure", "แปลงหน่วยความดัน Pa, bar, psi, kgf/cm², atm"),
}
CALC_GROUP_SCRIPTS = {"calculators": "js/tools_calculators.js", "engineering": "js/tools_engineering.js"}


def ph_diagram_data(request):
    if request.method != "GET":
        return HttpResponse(status=405)
    from .ph_diagram import calculate
    try:
        return JsonResponse(calculate(request.GET))
    except ValueError as exc:
        # Do not expose CoolProp internals for unsupported thermodynamic states.
        message = str(exc)
        if not any('\u0e00' <= char <= '\u0e7f' for char in message):
            message = "ค่านี้อยู่นอกช่วงที่คำนวณสถานะอิ่มตัวได้ กรุณาตรวจความดันและอุณหภูมิ"
        return JsonResponse({"error": message}, status=400)


def calc_tool(request, group, tool):
    if group == "engineering" and tool == "saturation-temp":
        return render(request, "utilities/saturation_temp.html", {
            "tool_icon_urls": _tool_icon_urls(),
        })
    spec = CALC_TOOLS.get(tool)
    if not spec or spec[0] != group:
        raise Http404
    _group, title, description = spec
    return render(request, "utilities/calc_tool.html", {
        "tool_key": tool,
        "tool_title": title,
        "tool_description": description,
        "panel_template": f"utilities/calc/{tool}.html",
        "tool_script": CALC_GROUP_SCRIPTS[group],
        "tool_icon_urls": _tool_icon_urls(),
    })


def calc_group_redirect(request, group):
    """The old combined Calculators / Engineering pages (?tab=...) now forward to the single-tool page."""
    tool = request.GET.get("tab", "")
    if CALC_TOOLS.get(tool, ("",))[0] == group:
        return redirect(f"utilities:{group}_tool", tool=tool)
    return redirect("utilities:index")
