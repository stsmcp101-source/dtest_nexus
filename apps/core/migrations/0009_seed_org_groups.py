from django.db import migrations

GROUPS = ["DT", "RAC", "PAC", "SOUND", "EMC", "SAMPLING", "SUPPORT", "ISO"]


def seed(apps, schema_editor):
    OrgGroup = apps.get_model("core", "OrgGroup")
    for order, name in enumerate(GROUPS, start=1):
        OrgGroup.objects.get_or_create(
            code=name.lower(), defaults={"name": name, "order": order}
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0008_orggroup")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
