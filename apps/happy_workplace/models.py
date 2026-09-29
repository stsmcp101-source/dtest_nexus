from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class HappyWorkplacePlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_happyworkplaceplaceholder", "Can view happy workplace module")]


class Announcement(models.Model):
    class Category(models.TextChoices):
        NEWS = "news", "ข่าวสาร"
        EVENT = "event", "กิจกรรม"
        NOTICE = "notice", "ประกาศ"

    title = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.NEWS)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class PosterImage(models.Model):
    """A poster/media image for the Happy Workplace bulletin board (left
    panel). Any common image format works (jpg/png/webp/gif/...) since
    Django's ImageField only validates that Pillow can read it."""

    image = models.ImageField(upload_to="happy_workplace/posters/")
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.caption or f"Poster #{self.pk}"


class FortuneSlip(models.Model):
    """One เซียมซี fortune slip image (the full illustrated slip — poem,
    translation, table — as a single uploaded picture). If none are
    uploaded, the game falls back to its built-in text fortunes."""

    order = models.PositiveSmallIntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="เลขที่ใบ 1-28",
    )
    image = models.ImageField(upload_to="happy_workplace/fortunes/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"ใบที่ {self.order}"


class GameScore(models.Model):
    """Shared leaderboard row for the simple score games (Squares, typing
    test). `game` is a key from views.GAME_SCORE_RULES, `detail` a short
    display string (best tile, accuracy...)."""

    game = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=25)
    score = models.PositiveIntegerField()
    detail = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "created_at"]


class HappyWorkplaceSettings(models.Model):
    """Singleton (pk=1): module-wide rules an admin can tune."""

    wordle_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    squares_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    typing_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    fortune_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    phone_analysis_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])
    dream_play_limit = models.PositiveSmallIntegerField(default=3, validators=[MaxValueValidator(100)])

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def limit_for(self, game):
        """Rounds allowed per browser per day for `game` (0 = unlimited)."""
        return getattr(self, f"{game}_play_limit")


class GamePlay(models.Model):
    """How many rounds one browser (anonymous client id) started in a game today."""

    game = models.CharField(max_length=20)
    client_id = models.CharField(max_length=36, db_index=True)
    day = models.DateField(db_index=True)
    count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["game", "client_id", "day"], name="uniq_gameplay_per_day")]


class SquaresWord(models.Model):
    """One entry in the Squares word bank (A-Z only, 3-12 letters)."""

    class Category(models.TextChoices):
        WORK = "W", "การทำงานและสำนักงาน"
        FOOD = "F", "อาหารและเครื่องดื่ม"
        TRAVEL = "T", "การเดินทางและการท่องเที่ยว"
        HEALTH = "H", "สุขภาพและการแพทย์"
        EMOTION = "E", "อารมณ์และความรู้สึก"
        CLOTHING = "C", "เครื่องแต่งกายและเครื่องประดับ"

    word = models.CharField(max_length=12, unique=True)
    meaning = models.CharField(max_length=200)
    category = models.CharField(max_length=1, choices=Category.choices, default=Category.WORK)

    class Meta:
        ordering = ["word"]

    def save(self, *args, **kwargs):
        self.word = self.word.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.word


class SquaresSettings(models.Model):
    """Singleton (pk=1) holding the Squares rules an admin can tune."""

    session_minutes = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WordleSettings(models.Model):
    """Singleton (pk=1) holding the Wordle rules an admin can tune."""

    session_minutes = models.PositiveSmallIntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )
    max_guesses = models.PositiveSmallIntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    penalty_per_wrong = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TypingSettings(models.Model):
    """Singleton (pk=1) holding the Typing Test rules an admin can tune."""

    session_minutes = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(60)]
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WordleScore(models.Model):
    name = models.CharField(max_length=30)
    score = models.PositiveIntegerField()
    words_correct = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-words_correct", "created_at"]
