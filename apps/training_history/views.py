import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.documents.storage import validate_upload
from apps.permissions.decorators import require_permission
from apps.permissions.registry import user_has

from .models import TrainingEmployee, TrainingRecord

PHOTO_MAX_MB = 5
DOC_MAX_MB = 10


@login_required
@require_permission("internal.view")
def index(request):
    employees = TrainingEmployee.objects.all()
    trainings = TrainingRecord.objects.select_related("employee").all()
    context = {
        "can_edit": user_has(request.user, "internal.training_edit"),
        "employees_data": [e.as_dict() for e in employees],
        "trainings_data": [t.as_dict() for t in trainings],
        "employee_count": employees.count(),
    }
    return render(request, "training_history/index.html", context)


def _clean_str(value, max_len=None):
    s = str(value or "").strip()
    return s[:max_len] if max_len else s


def _clean_status(value):
    status = _clean_str(value).lower()
    return status if status in TrainingEmployee.Status.values else None


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_employee_create(request):
    emp_id = _clean_str(request.POST.get("empId"), 20)
    history_no = _clean_str(request.POST.get("historyNo"), 30)
    name_th = _clean_str(request.POST.get("nameTh"), 150)
    name_en = _clean_str(request.POST.get("nameEn"), 150)

    if not emp_id or not history_no or not name_th or not name_en:
        return JsonResponse({"ok": False, "message": "กรุณากรอกข้อมูลที่จำเป็นให้ครบ"}, status=400)
    if TrainingEmployee.objects.filter(emp_id=emp_id).exists():
        return JsonResponse({"ok": False, "message": f"รหัสพนักงาน {emp_id} มีอยู่แล้ว"}, status=400)
    if TrainingEmployee.objects.filter(history_no=history_no).exists():
        return JsonResponse({"ok": False, "message": f"เลขที่ประวัติ {history_no} มีอยู่แล้ว"}, status=400)
    emp_status = _clean_status(request.POST.get("status") or TrainingEmployee.Status.ACTIVE)
    if not emp_status:
        return JsonResponse({"ok": False, "message": "สถานะพนักงานไม่ถูกต้อง"}, status=400)

    photo = request.FILES.get("photo")
    if photo:
        try:
            validate_upload(photo, ["png", "jpg", "jpeg", "webp"], PHOTO_MAX_MB)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "message": str(exc.message)}, status=400)

    employee = TrainingEmployee.objects.create(
        emp_id=emp_id, history_no=history_no, name_th=name_th, name_en=name_en,
        working_group=_clean_str(request.POST.get("group"), 50),
        position=_clean_str(request.POST.get("position"), 30),
        education=_clean_str(request.POST.get("education"), 200),
        work_start_date=parse_date(request.POST.get("workStart") or ""),
        birth_date=parse_date(request.POST.get("birthday") or ""),
        status=emp_status,
        photo=photo,
    )

    log_action(
        user=request.user, action="CREATE", module="training_history", object_type="TrainingEmployee",
        object_id=employee.pk, description=f"เพิ่มพนักงาน {employee.emp_id} — {employee.name_en}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "employee": employee.as_dict()})


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_employee_update(request, pk):
    employee = get_object_or_404(TrainingEmployee, pk=pk)
    name_th = _clean_str(request.POST.get("nameTh"), 150)
    name_en = _clean_str(request.POST.get("nameEn"), 150)
    if not name_th or not name_en:
        return JsonResponse({"ok": False, "message": "กรุณากรอกข้อมูลที่จำเป็นให้ครบ"}, status=400)
    emp_status = _clean_status(request.POST.get("status") or employee.status)
    if not emp_status:
        return JsonResponse({"ok": False, "message": "สถานะพนักงานไม่ถูกต้อง"}, status=400)

    photo = request.FILES.get("photo")
    if photo:
        try:
            validate_upload(photo, ["png", "jpg", "jpeg", "webp"], PHOTO_MAX_MB)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "message": str(exc.message)}, status=400)

    employee.name_th = name_th
    employee.name_en = name_en
    employee.working_group = _clean_str(request.POST.get("group"), 50)
    employee.position = _clean_str(request.POST.get("position"), 30)
    employee.education = _clean_str(request.POST.get("education"), 200)
    employee.work_start_date = parse_date(request.POST.get("workStart") or "")
    employee.birth_date = parse_date(request.POST.get("birthday") or "")
    employee.status = emp_status
    if photo:
        if employee.photo:
            employee.photo.delete(save=False)
        employee.photo = photo
    elif request.POST.get("removePhoto") == "1" and employee.photo:
        employee.photo.delete(save=False)
    employee.save()

    log_action(
        user=request.user, action="UPDATE", module="training_history", object_type="TrainingEmployee",
        object_id=employee.pk, description=f"แก้ไขพนักงาน {employee.emp_id} — {employee.name_en}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "employee": employee.as_dict()})


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_employee_delete(request, pk):
    employee = get_object_or_404(TrainingEmployee, pk=pk)
    emp_id, name_en = employee.emp_id, employee.name_en
    training_count = employee.trainings.count()
    if employee.photo:
        employee.photo.delete(save=False)
    for record in employee.trainings.all():
        if record.evidence_file:
            record.evidence_file.delete(save=False)
    employee.delete()

    log_action(
        user=request.user, action="DELETE", module="training_history", object_type="TrainingEmployee",
        object_id=pk, description=f"ลบพนักงาน {emp_id} — {name_en} (พร้อมประวัติการอบรม {training_count} รายการ)",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "empId": emp_id})


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_training_create(request):
    emp_id = _clean_str(request.POST.get("empId"), 20)
    course_name = _clean_str(request.POST.get("courseName"), 300)
    training_date = _clean_str(request.POST.get("trainingDate"), 60)
    trainer = _clean_str(request.POST.get("trainer"), 200)

    if not emp_id or not course_name or not training_date or not trainer:
        return JsonResponse({"ok": False, "message": "กรุณากรอกข้อมูลที่จำเป็นให้ครบ"}, status=400)

    employee = TrainingEmployee.objects.filter(emp_id=emp_id).first()
    if not employee:
        return JsonResponse({"ok": False, "message": "ไม่พบพนักงานที่เลือก"}, status=400)

    evidence_file = request.FILES.get("docFile")
    if evidence_file:
        try:
            validate_upload(evidence_file, ["png", "jpg", "jpeg", "webp", "pdf"], DOC_MAX_MB)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "message": str(exc.message)}, status=400)

    next_no = employee.trainings.count() + 1
    ref_id = _clean_str(request.POST.get("refId"), 50) or f"{employee.history_no}-{next_no:02d}"

    record = TrainingRecord.objects.create(
        employee=employee, course_name=course_name, training_date=training_date, trainer=trainer,
        evidence_label=_clean_str(request.POST.get("evidence"), 100) or "Certificate",
        recorder=_clean_str(request.POST.get("recorder"), 100),
        record_date=_clean_str(request.POST.get("recordDate"), 60),
        ref_id=ref_id,
        evidence_file=evidence_file,
    )

    log_action(
        user=request.user, action="CREATE", module="training_history", object_type="TrainingRecord",
        object_id=record.pk, description=f"บันทึกการอบรม {record.course_name} ให้ {employee.emp_id}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "training": record.as_dict()})


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_training_update(request, pk):
    record = get_object_or_404(TrainingRecord, pk=pk)
    emp_id = _clean_str(request.POST.get("empId"), 20)
    course_name = _clean_str(request.POST.get("courseName"), 300)
    training_date = _clean_str(request.POST.get("trainingDate"), 60)
    trainer = _clean_str(request.POST.get("trainer"), 200)

    if not emp_id or not course_name or not training_date or not trainer:
        return JsonResponse({"ok": False, "message": "กรุณากรอกข้อมูลที่จำเป็นให้ครบ"}, status=400)

    employee = TrainingEmployee.objects.filter(emp_id=emp_id).first()
    if not employee:
        return JsonResponse({"ok": False, "message": "ไม่พบพนักงานที่เลือก"}, status=400)

    evidence_file = request.FILES.get("docFile")
    if evidence_file:
        try:
            validate_upload(evidence_file, ["png", "jpg", "jpeg", "webp", "pdf"], DOC_MAX_MB)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "message": str(exc.message)}, status=400)

    record.employee = employee
    record.course_name = course_name
    record.training_date = training_date
    record.trainer = trainer
    record.evidence_label = _clean_str(request.POST.get("evidence"), 100) or "Certificate"
    record.recorder = _clean_str(request.POST.get("recorder"), 100)
    record.record_date = _clean_str(request.POST.get("recordDate"), 60)
    record.ref_id = _clean_str(request.POST.get("refId"), 50) or record.ref_id
    if evidence_file:
        if record.evidence_file:
            record.evidence_file.delete(save=False)
        record.evidence_file = evidence_file
    record.save()

    log_action(
        user=request.user, action="UPDATE", module="training_history", object_type="TrainingRecord",
        object_id=record.pk, description=f"แก้ไขการอบรม {record.course_name} ของ {employee.emp_id}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "training": record.as_dict()})


@login_required
@require_permission("internal.training_edit")
@require_POST
def api_training_delete(request, pk):
    record = get_object_or_404(TrainingRecord, pk=pk)
    emp_id, course_name = record.employee.emp_id, record.course_name
    if record.evidence_file:
        record.evidence_file.delete(save=False)
    record.delete()

    log_action(
        user=request.user, action="DELETE", module="training_history", object_type="TrainingRecord",
        object_id=pk, description=f"ลบการอบรม {course_name} ของ {emp_id}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, "id": pk})
