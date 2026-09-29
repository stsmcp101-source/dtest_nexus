import json
from pathlib import Path

from django.db import migrations

SEED_PATH = Path(__file__).resolve().parent / "seed_data.json"


def seed_data(apps, schema_editor):
    SparePart = apps.get_model("spare_parts", "SparePart")
    SparePartTransaction = apps.get_model("spare_parts", "SparePartTransaction")

    if SparePart.objects.exists():
        return

    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    parts_by_pn = {}
    for row in data["parts"]:
        part = SparePart.objects.create(
            pn=row["pn"], desc=row.get("desc", ""), descth=row.get("descth", ""),
            cat=row.get("cat", ""), sub=row.get("sub", ""), mfr=row.get("mfr", ""),
            model=row.get("model", ""), unit=row.get("unit") or "EA",
            price=row.get("price") or 0,
            min_stock=row.get("min") or 0, cur_stock=row.get("cur") or 0, max_stock=row.get("max") or 0,
            location=row.get("loc", ""), lead_time_days=str(row.get("lead") or ""),
            remarks=row.get("remarks", ""),
        )
        parts_by_pn[part.pn] = part

    for row in data["txlog"]:
        SparePartTransaction.objects.create(
            part=parts_by_pn.get(row["pn"]),
            pn=row["pn"], desc=row.get("desc", ""), tx_type=row["type"],
            delta=row.get("delta", 0), before=row.get("before", 0), after=row.get("after", 0),
            by=row.get("by", ""), reason=row.get("reason", ""),
            occurred_label=row.get("ts", ""),
        )


def unseed_data(apps, schema_editor):
    SparePartTransaction = apps.get_model("spare_parts", "SparePartTransaction")
    SparePart = apps.get_model("spare_parts", "SparePart")
    SparePartTransaction.objects.all().delete()
    SparePart.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("spare_parts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
