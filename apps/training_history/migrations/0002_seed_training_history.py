from django.db import migrations

EMPLOYEES = [
    {"emp_id": "18221", "history_no": "ISO-M001", "name_th": "นาย เอกลักษณ์ เชยชม", "name_en": "Mr.Ekkaluck Choeichom",
     "group": "ISO 17025", "position": "S5", "education": "ปริญญาตรี ( วิศวกรรมเครื่องกล )",
     "work_start": "2018-08-01", "birth": "1983-01-23"},
    {"emp_id": "18222", "history_no": "ISO-M002", "name_th": "นาย สราวุฒิ ทิศพัน", "name_en": "Mr.Sarawut Thitfan",
     "group": "ISO 17025", "position": "S1", "education": "ปวส. ( ไฟฟ้ากำลัง )",
     "work_start": "2021-06-16", "birth": "1995-10-31"},
    {"emp_id": "18223", "history_no": "ISO-M003", "name_th": "นาย เนรัญชลา สายเสือ", "name_en": "Mr.Neranchala Saisua",
     "group": "EMC", "position": "S4", "education": "ปวส. ( อิเล็คทรอนิกส์ )",
     "work_start": "2010-11-01", "birth": "1984-08-22"},
    {"emp_id": "18224", "history_no": "ISO-M004", "name_th": "นาย สุริยา รักษา", "name_en": "Mr.Suriya Raksa",
     "group": "EMC", "position": "S3", "education": "ปวส. ( อิเล็คทรอนิกส์ )",
     "work_start": "2015-07-01", "birth": "1989-06-19"},
    {"emp_id": "18225", "history_no": "ISO-M005", "name_th": "นาย ศิระสิทธิ์ อุ่นใจเรือน", "name_en": "Mr.Sirasith Ounjairuen",
     "group": "EMC", "position": "S3", "education": "ปวส. ( ไฟฟ้ากำลัง )",
     "work_start": "2019-09-05", "birth": "1996-03-23"},
    {"emp_id": "18226", "history_no": "ISO-M006", "name_th": "นาย จักรพันธ์ วันตะนัตถัง", "name_en": "Mr.Chakkaphan Wantanatong",
     "group": "EMC", "position": "S3", "education": "ปวส. ( ไฟฟ้ากำลัง )",
     "work_start": "2021-06-16", "birth": "1993-01-15"},
    {"emp_id": "18227", "history_no": "ISO-M007", "name_th": "นาย ปรัชญา แก้วเครือ", "name_en": "Mr.Pratchaya Kauwkrue",
     "group": "EMC", "position": "S2", "education": "ปวส. ( ไฟฟ้ากำลัง )",
     "work_start": "2023-08-01", "birth": "2001-03-29"},
    {"emp_id": "18228", "history_no": "ISO-M008", "name_th": "นาย ธีรวัฒน์ แสนหอม", "name_en": "Mr.Teerawat Sanhom",
     "group": "SAMPLING", "position": "S4", "education": "ปวส. ( ไฟฟ้ากำลัง )",
     "work_start": "2003-03-10", "birth": "1981-05-04"},
    {"emp_id": "18229", "history_no": "ISO-M009", "name_th": "นาย อานนท์ นรสิงห์น้อย", "name_en": "Mr.Arnont Norsungnoen",
     "group": "SOUND", "position": "S2", "education": "ม.6 ( วิทย์-คณิต )",
     "work_start": "1996-05-16", "birth": "1975-02-25"},
    {"emp_id": "18230", "history_no": "ISO-M010", "name_th": "นาย ชัยพฤกษ์ ทองแปง", "name_en": "Mr.Chaiyapruek Thongpaeng",
     "group": "SOUND", "position": "S4", "education": "ปวส. ( อิเล็คทรอนิกส์ )",
     "work_start": "2014-02-17", "birth": "1992-05-13"},
]

TRAININGS = [
    {"emp_id": "18221", "course_name": "การจัดทำระบบคุณภาพห้องปฏิบัติการตาม มาตรฐาน ISO/IEC 14025 : 2017", "training_date": "22-Aug-2018", "trainer": "สำนักงานมาตรฐานผลิตภัณฑ์", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-01"},
    {"emp_id": "18221", "course_name": "Understanding of ISO/IEC 17025 : 2017 Laboratory Standard Requirements", "training_date": "11-Dec-2018", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-02"},
    {"emp_id": "18221", "course_name": "Preparing for quality management system documentation according to ISO/IEC 17025 : 2017", "training_date": "12-Dec-2018", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-03"},
    {"emp_id": "18221", "course_name": "Basics of estimating measurement uncertainty", "training_date": "17-Dec-2018", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-04"},
    {"emp_id": "18221", "course_name": "Basics statistics for ISO/IEC 17025 : 2017", "training_date": "18-Dec-2018", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-05"},
    {"emp_id": "18221", "course_name": "ความปลอดภัยในการทำงานเกี่ยวกับไฟฟ้า และผ่านเกณฑ์การวัดผลและประเมินผล", "training_date": "31-Jan-2019", "trainer": "นายธีรเทพ พราหมณ์มณี / MCP", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-06"},
    {"emp_id": "18221", "course_name": "Introduction to ISO/IEC 17025", "training_date": "26-27-Sep-2022", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-07"},
    {"emp_id": "18221", "course_name": "ISO/IEC 17025 Internal Auditor", "training_date": "4-Oct-2022", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-08"},
    {"emp_id": "18221", "course_name": "Statistics for evaluation & Comparison of measurement results", "training_date": "21-Oct-2022", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-09"},
    {"emp_id": "18221", "course_name": "Measurement Uncertainty", "training_date": "14-Nov-2022", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-10"},
    {"emp_id": "18221", "course_name": "Training Program GMA overview, Performance for Middle East and UL standard UL 60335-2-40", "training_date": "29-Apr-2024", "trainer": "UL Solution", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M001-11"},
    {"emp_id": "18221", "course_name": "ISO/IEC 17025 Introduction and Internal Auditor Course", "training_date": "15-16,23-Apr-2025", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "2-Aug-2025", "ref_id": "ISO-M001-12"},
    {"emp_id": "18221", "course_name": "Statistics for evaluation & Comparison of measurement results", "training_date": "01-Aug-2025", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "14-Aug-2025", "ref_id": "ISO-M001-13"},
    {"emp_id": "18221", "course_name": "Uncertainty of Measurement Course", "training_date": "05-Sep-2025", "trainer": "Mr.Somporn Boonlert / MASCI", "recorder": "Sarawut T.", "record_date": "11-Sep-2025", "ref_id": "ISO-M001-14"},
    {"emp_id": "18222", "course_name": "Understanding of ISO/IEC 17025 : 2017 Laboratory Standard Requirements", "training_date": "16-Jul-2021", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M002-01"},
    {"emp_id": "18223", "course_name": "EMC Testing Standards & Measurement Principles", "training_date": "10-Nov-2020", "trainer": "TISTR", "recorder": "Sarawut T.", "record_date": "1-Oct-2024", "ref_id": "ISO-M003-01"},
]


def seed_data(apps, schema_editor):
    TrainingEmployee = apps.get_model("training_history", "TrainingEmployee")
    TrainingRecord = apps.get_model("training_history", "TrainingRecord")

    if TrainingEmployee.objects.exists():
        return

    by_emp_id = {}
    for row in EMPLOYEES:
        emp = TrainingEmployee.objects.create(
            emp_id=row["emp_id"], history_no=row["history_no"],
            name_th=row["name_th"], name_en=row["name_en"],
            working_group=row["group"], position=row["position"], education=row["education"],
            work_start_date=row["work_start"], birth_date=row["birth"], status="active",
        )
        by_emp_id[emp.emp_id] = emp

    for row in TRAININGS:
        employee = by_emp_id.get(row["emp_id"])
        if not employee:
            continue
        TrainingRecord.objects.create(
            employee=employee, course_name=row["course_name"], training_date=row["training_date"],
            trainer=row["trainer"], evidence_label="Certificate",
            recorder=row["recorder"], record_date=row["record_date"], ref_id=row["ref_id"],
        )


def unseed_data(apps, schema_editor):
    TrainingRecord = apps.get_model("training_history", "TrainingRecord")
    TrainingEmployee = apps.get_model("training_history", "TrainingEmployee")
    TrainingRecord.objects.all().delete()
    TrainingEmployee.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("training_history", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
