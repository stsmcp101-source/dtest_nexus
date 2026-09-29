from datetime import date

from django.db import models


class TrainingEmployee(models.Model):
    """One employee tracked for external training history."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESIGNED = "resigned", "Resigned"

    emp_id = models.CharField("รหัสพนักงาน", max_length=20, unique=True)
    history_no = models.CharField("เลขที่ประวัติ", max_length=30, unique=True)
    name_th = models.CharField("ชื่อภาษาไทย", max_length=150)
    name_en = models.CharField("ชื่อภาษาอังกฤษ", max_length=150)
    working_group = models.CharField("กลุ่มงาน", max_length=50, blank=True)
    position = models.CharField("ตำแหน่งงาน", max_length=30, blank=True)
    education = models.CharField("วุฒิการศึกษา", max_length=200, blank=True)
    work_start_date = models.DateField("วันที่เริ่มงาน", null=True, blank=True)
    birth_date = models.DateField("วันที่เกิด", null=True, blank=True)
    status = models.CharField("สถานะพนักงาน", max_length=10, choices=Status.choices, default=Status.ACTIVE)
    photo = models.ImageField("รูปถ่ายพนักงาน", upload_to="training_history/employees/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["emp_id"]

    def __str__(self):
        return f"{self.emp_id} — {self.name_en}"

    @staticmethod
    def _years_between(start, end):
        if not start:
            return None
        years = end.year - start.year
        if (end.month, end.day) < (start.month, start.day):
            years -= 1
        return max(0, years)

    @property
    def work_years(self):
        return self._years_between(self.work_start_date, date.today())

    @property
    def age(self):
        return self._years_between(self.birth_date, date.today())

    def as_dict(self):
        return {
            "id": self.pk,
            "empId": self.emp_id,
            "historyNo": self.history_no,
            "nameTh": self.name_th,
            "nameEn": self.name_en,
            "group": self.working_group,
            "position": self.position,
            "education": self.education,
            "workStart": self.work_start_date.isoformat() if self.work_start_date else "",
            "workStartDisplay": thai_date(self.work_start_date),
            "workYears": self.work_years,
            "birthday": self.birth_date.isoformat() if self.birth_date else "",
            "birthdayDisplay": thai_date(self.birth_date),
            "age": self.age,
            "status": self.get_status_display(),
            "statusCode": self.status,
            "photoUrl": self.photo.url if self.photo else "",
        }


THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def thai_date(d):
    if not d:
        return ""
    return f"{d.day} {THAI_MONTHS[d.month - 1]} {d.year + 543}"


class TrainingRecord(models.Model):
    """One external training course an employee completed."""

    employee = models.ForeignKey(TrainingEmployee, on_delete=models.CASCADE, related_name="trainings")
    course_name = models.CharField("หลักสูตรที่อบรม", max_length=300)
    training_date = models.CharField("วันที่อบรม", max_length=60)
    trainer = models.CharField("ผู้ฝึกอบรม / สถาบัน", max_length=200)
    evidence_label = models.CharField("หลักฐานผ่านการอบรม", max_length=100, default="Certificate")
    recorder = models.CharField("ผู้บันทึก", max_length=100, blank=True)
    record_date = models.CharField("วันที่บันทึก", max_length=60, blank=True)
    ref_id = models.CharField("อ้างอิงเอกสาร/รูป", max_length=50, blank=True)
    evidence_file = models.FileField("ไฟล์หลักฐาน", upload_to="training_history/evidence/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employee__emp_id", "id"]

    def __str__(self):
        return f"{self.employee.emp_id} — {self.course_name}"

    @property
    def evidence_type(self):
        if not self.evidence_file:
            return ""
        name = self.evidence_file.name.lower()
        return "pdf" if name.endswith(".pdf") else "image"

    def as_dict(self):
        return {
            "id": self.pk,
            "empId": self.employee.emp_id,
            "courseName": self.course_name,
            "trainingDate": self.training_date,
            "trainer": self.trainer,
            "evidence": self.evidence_label,
            "recorder": self.recorder,
            "recordDate": self.record_date,
            "refId": self.ref_id,
            "docUrl": self.evidence_file.url if self.evidence_file else "",
            "docType": self.evidence_type,
        }
