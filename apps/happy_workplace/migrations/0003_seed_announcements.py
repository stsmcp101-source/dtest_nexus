from django.db import migrations


def seed_announcements(apps, schema_editor):
    Announcement = apps.get_model("happy_workplace", "Announcement")
    if Announcement.objects.exists():
        return
    Announcement.objects.bulk_create([
        Announcement(
            title="เปิดตัวโซน Happy Workplace อย่างเป็นทางการ",
            body="พื้นที่พักผ่อนสมองใหม่สำหรับชาว dTest.nexus มาพร้อมข่าวสารกิจกรรมและมินิเกมคลายเครียดให้เล่นกันในเวลาว่าง",
            category="news",
            is_pinned=True,
        ),
        Announcement(
            title="กิจกรรมวันกีฬาสีประจำปี",
            body="เตรียมตัวให้พร้อม! กิจกรรมกีฬาสีประจำปีของบริษัทกำลังจะมาถึง ติดตามรายละเอียดทีมและตารางแข่งขันเร็ว ๆ นี้",
            category="event",
        ),
        Announcement(
            title="แจ้งปิดปรับปรุงระบบเอกสารช่วงสุดสัปดาห์",
            body="ระบบ Document Data จะปิดปรับปรุงชั่วคราวเพื่อบำรุงรักษา แจ้งเตือนล่วงหน้าอีกครั้งก่อนวันจริง",
            category="notice",
        ),
    ])


class Migration(migrations.Migration):

    dependencies = [
        ("happy_workplace", "0002_announcement"),
    ]

    operations = [
        migrations.RunPython(seed_announcements, migrations.RunPython.noop),
    ]
