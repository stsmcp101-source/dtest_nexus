from django.db import migrations

from apps.happy_workplace.squares_words import WORDS


def seed(apps, schema_editor):
    SquaresWord = apps.get_model("happy_workplace", "SquaresWord")
    SquaresWord.objects.all().delete()
    SquaresWord.objects.bulk_create(
        [SquaresWord(word=word, category=category, meaning=meaning) for word, category, meaning in WORDS],
        ignore_conflicts=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("happy_workplace", "0013_per_game_play_limit")]
    operations = [migrations.RunPython(seed, noop)]
