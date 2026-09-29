from django.db import migrations


def seed(apps, schema_editor):
    from apps.happy_workplace.squares_words import WORDS

    SquaresWord = apps.get_model("happy_workplace", "SquaresWord")
    GameScore = apps.get_model("happy_workplace", "GameScore")
    for word, category, meaning in WORDS:
        SquaresWord.objects.get_or_create(word=word, defaults={"meaning": meaning, "category": category})
    GameScore.objects.filter(game="game_2048").delete()


class Migration(migrations.Migration):
    dependencies = [("happy_workplace", "0010_squares_models")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
