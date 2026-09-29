import django.core.validators
from django.db import migrations, models


def copy_old_limit(apps, schema_editor):
    Settings = apps.get_model("happy_workplace", "HappyWorkplaceSettings")
    for row in Settings.objects.all():
        row.wordle_play_limit = row.squares_play_limit = row.typing_play_limit = row.daily_play_limit
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ('happy_workplace', '0012_play_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='happyworkplacesettings',
            name='squares_play_limit',
            field=models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='happyworkplacesettings',
            name='typing_play_limit',
            field=models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='happyworkplacesettings',
            name='wordle_play_limit',
            field=models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.RunPython(copy_old_limit, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='happyworkplacesettings',
            name='daily_play_limit',
        ),
    ]
