from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import migrations

# (name, hover text, logo file in static/img/standards/, link)
STANDARDS = [
    ("EGAT No.5", "EGAT No.5 — ประหยัดไฟเบอร์ 5", "egat-no5.png", "https://labelno5.egat.co.th/home/labelno5/"),
    ("มอก. (TISI)", "มอก. — มาตรฐานผลิตภัณฑ์อุตสาหกรรม", "tisi.png", "https://www.tisi.go.th/website/standardlist/comp_thai/th"),
    (
        "AHRI", "AHRI Certified", "ahri.png",
        "https://www.ahrinet.org/search-standards/ahri-210240-i-p-performance-rating-unitary-air-conditioning-and-air-source-heat-pump-equipment",
    ),
    ("ISO/IEC 17025", "ILAC-MRA / NSC-TISI-TIS 17025 Calibration", "ilac-nsc.png", ""),
]


def seed(apps, schema_editor):
    Standard = apps.get_model("core", "Standard")
    if Standard.objects.exists():
        return
    for order, (name, description, filename, url) in enumerate(STANDARDS, start=1):
        # Fixed media name, copied only once, so re-running migrations (e.g. the test DB) doesn't pile up copies.
        logo_name = f"standards/{filename}"
        if not default_storage.exists(logo_name):
            with open(settings.BASE_DIR / "static" / "img" / "standards" / filename, "rb") as f:
                logo_name = default_storage.save(logo_name, File(f))
        Standard.objects.create(name=name, description=description, logo=logo_name, url=url, order=order)


def unseed(apps, schema_editor):
    apps.get_model("core", "Standard").objects.filter(name__in=[s[0] for s in STANDARDS]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0012_standard")]
    operations = [migrations.RunPython(seed, unseed)]
