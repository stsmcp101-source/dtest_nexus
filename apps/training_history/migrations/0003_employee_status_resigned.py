from django.db import migrations, models


def inactive_to_resigned(apps, schema_editor):
    TrainingEmployee = apps.get_model("training_history", "TrainingEmployee")
    TrainingEmployee.objects.filter(status="inactive").update(status="resigned")


def resigned_to_inactive(apps, schema_editor):
    TrainingEmployee = apps.get_model("training_history", "TrainingEmployee")
    TrainingEmployee.objects.filter(status="resigned").update(status="inactive")


class Migration(migrations.Migration):

    dependencies = [
        ("training_history", "0002_seed_training_history"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trainingemployee",
            name="status",
            field=models.CharField(
                choices=[("active", "Active"), ("resigned", "Resigned")],
                default="active",
                max_length=10,
                verbose_name="สถานะพนักงาน",
            ),
        ),
        migrations.RunPython(inactive_to_resigned, resigned_to_inactive),
    ]
