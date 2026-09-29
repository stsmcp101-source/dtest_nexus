from django.db import migrations

TOPICS = [
    ("policy", "Policy", "นโยบาย", "ให้ทุกแผนกใช้ข้อมูลและเอกสารชุดเดียวกัน ถูกต้อง เป็นปัจจุบัน และเข้าถึงได้ตามสิทธิ์ที่เหมาะสมกับหน้าที่ของแต่ละคน"),
    ("vision", "Vision", "วิสัยทัศน์", "เป็นศูนย์กลางข้อมูลของสายงานพัฒนาและขยายผลิตภัณฑ์เครื่องปรับอากาศ ที่ทำให้การทำงานร่วมกันโปร่งใส ตรวจสอบได้ และต่อยอดได้"),
    ("objective", "Objective", "วัตถุประสงค์", "รวมเอกสาร ข้อมูลบุคคล ใบรับรอง และผลการทดสอบไว้ในระบบเดียว ลดงานซ้ำซ้อน และเพิ่มความรวดเร็วในการค้นหาและติดตามงาน"),
    ("kpi", "KPI", "ตัวชี้วัด", "ติดตามจากจำนวนเอกสารในระบบ ยอดเข้าใช้งาน และความครอบคลุมของการใช้งานในแต่ละกลุ่มงาน (รายละเอียดตัวชี้วัดอยู่ระหว่างจัดทำ)"),
    ("contact", "Contact", "ติดต่อ", "สอบถามการใช้งาน แจ้งปัญหา หรือขอสิทธิ์เข้าถึงระบบได้ที่ผู้ดูแลระบบ dTest.nexus (รายละเอียดช่องทางติดต่ออยู่ระหว่างจัดทำ)"),
]


def seed(apps, schema_editor):
    AboutTopic = apps.get_model("core", "AboutTopic")
    for order, (code, en, th, body) in enumerate(TOPICS, start=1):
        AboutTopic.objects.get_or_create(
            code=code, defaults={"title_en": en, "title_th": th, "body": body, "order": order}
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0006_abouttopic")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
