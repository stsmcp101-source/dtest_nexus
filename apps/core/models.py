from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone


class SystemSettings(models.Model):
    """
    Singleton-style configuration row editable from the app UI (as
    opposed to environment variables, which hold secrets/infra config).
    Enforced as a singleton by always using pk=1 (see get_solo()).
    """

    site_display_name = models.CharField(max_length=150, default="dTest.nexus")
    support_email = models.EmailField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)

    # Home page hero background, uploaded here rather than dropped into
    # static/img/home/ — uploads get a fresh media URL each time, so
    # browsers can't serve a stale cached copy the way they could with
    # a static file overwritten in place. If left blank, the home view
    # falls back to auto-detecting a static/img/home/hero-bg.* file.
    hero_bg_image = models.ImageField(upload_to="hero/", blank=True, null=True)
    hero_bg_video = models.FileField(upload_to="hero/", blank=True, null=True)

    # External system links surfaced as tiles on the Tools page (Systems
    # section). Editable here rather than hard-coded so an administrator
    # can set/change them without a code deploy, same rationale as
    # ModuleDefinition.
    tool_link_approve_doc = models.URLField(
        blank=True, help_text="Power Apps link for the Tools > Systems > Approve Doc tile."
    )
    tool_link_kace = models.URLField(
        blank=True, help_text="KACE Systems URL for the Tools > Systems tile."
    )
    tool_link_pscapa = models.URLField(
        blank=True, help_text="PScapa URL for the Tools > Systems tile."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
        permissions = []  # add_/change_/view_ auto-created -> settings.view / settings.edit

    def __str__(self):
        return "System Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ModuleDefinition(models.Model):
    """
    Registry row for each homepage/navigation module (Document Data,
    Employees, Certificates, ...). Lets an administrator toggle a
    module's visibility/availability without a code deploy, and gives
    the seed command a stable place to (re)create the canonical seven
    modules described in the HTML reference.
    """

    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    short_tag = models.CharField(max_length=20, help_text="e.g. DOC, HR, CERT")
    description = models.TextField(blank=True)
    url_name = models.CharField(max_length=100, help_text="Django URL name, e.g. 'documents:list'")
    icon_svg_path = models.TextField(
        blank=True, help_text="Inner <path>/<circle> markup for the module card icon (trusted, admin-authored)."
    )
    background_image = models.ImageField(
        upload_to="modules/", blank=True, null=True,
        help_text="Home page menu strip background photo. Falls back to the line icon above if left blank.",
    )
    background_image_speed = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text=(
            "Playback-speed multiplier applied when background_image is an animated GIF "
            "(>1 slows it down, <1 speeds it up, 1 = original speed). No effect on static images."
        ),
    )
    background_image_processed = models.ImageField(
        upload_to="modules/processed/", blank=True, null=True, editable=False,
        help_text="Auto-regenerated from background_image + background_image_speed — never set directly.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text="False = 'coming soon' styling on the home page")

    class Meta:
        ordering = ["order", "code"]

    def __str__(self):
        return self.name


class AboutTopic(models.Model):
    """One editable block of the home page's "เกี่ยวกับ dTest.nexus" section
    (Policy, Vision, ...). The About Us nav menu lists these same rows, so a
    renamed title shows up in both places. `code` is the fixed anchor id."""

    code = models.SlugField(max_length=30, unique=True)
    title_en = models.CharField(max_length=60, help_text="หัวข้อภาษาอังกฤษ (แสดงในเมนู About Us ด้วย)")
    title_th = models.CharField(max_length=60, blank=True, help_text="ชื่อภาษาไทยที่แสดงเล็กๆ ข้างหัวข้อ")
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to="about/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "code"]

    def __str__(self):
        return self.title_en


class Standard(models.Model):
    """One logo card in the home page's "มาตรฐาน รองรับ" section. The same
    rows fill the navbar's Standard > Testing STD. menu, so adding one in
    Admin shows up in both places."""

    name = models.CharField("ชื่อมาตรฐาน", max_length=80, help_text="แสดงในเมนู Standard และใช้เป็นข้อความแทนรูปโลโก้")
    description = models.CharField(
        "คำอธิบาย", max_length=200, blank=True, help_text="ข้อความที่แสดงเมื่อเอาเมาส์ชี้โลโก้ (เว้นว่างได้)"
    )
    logo = models.ImageField("รูปโลโก้", upload_to="standards/")
    url = models.URLField(
        "ลิงก์", max_length=500, blank=True,
        help_text="เปิดในแท็บใหม่เมื่อกดโลโก้หรือเมนู — เว้นว่างได้ ถ้าไม่มีลิงก์ โลโก้จะกดไม่ได้",
    )
    order = models.PositiveIntegerField("ลำดับ", default=0, help_text="เลขน้อยแสดงก่อน")
    is_active = models.BooleanField("แสดงผล", default=True, help_text="ปิดเพื่อซ่อนชั่วคราวโดยไม่ต้องลบ")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "มาตรฐาน (Standard)"
        verbose_name_plural = "มาตรฐาน (Standards)"

    def __str__(self):
        return self.name


class OrgGroup(models.Model):
    """One editable block of the home page's "โครงสร้างองค์กร" section.
    Mirrors AboutTopic: a short code, name, optional descriptive text, and
    an optional image, all editable from Settings without a code deploy."""

    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=60, help_text="ชื่อกลุ่มงาน เช่น DT, RAC, PAC")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="org/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "code"]

    def __str__(self):
        return self.name


class PageViewStat(models.Model):
    """
    One row per tracked page/menu (Home, and each active ModuleDefinition)
    — a running hit counter plus last-visited timestamp. Populated by
    apps.core.middleware.PageViewTrackingMiddleware on every successful
    page load, not per-request logic scattered across views, so adding a
    new module to ModuleDefinition gets tracked automatically.
    """

    key = models.SlugField(max_length=60, unique=True, db_index=True)
    label = models.CharField(max_length=120)
    count = models.PositiveBigIntegerField(default=0)
    last_visited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-count"]

    def __str__(self):
        return f"{self.label} — {self.count}"

    @classmethod
    def record_visit(cls, key, label):
        obj, created = cls.objects.get_or_create(key=key, defaults={"label": label})
        if not created and obj.label != label:
            obj.label = label
            obj.save(update_fields=["label"])
        cls.objects.filter(pk=obj.pk).update(count=F("count") + 1, last_visited_at=timezone.now())
        PageViewLog.objects.create(page_key=key, page_label=label)

    @classmethod
    def reset_all(cls):
        """Wipes both the running totals and the detail log behind the
        monthly summary — a full, clean restart of visit counting."""
        cls.objects.update(count=0, last_visited_at=None)
        PageViewLog.objects.all().delete()


class PageViewLog(models.Model):
    """
    One row per individual page view — the detail behind PageViewStat's
    running totals, kept specifically so usage can be summarised by
    month (or any other period) later without having guessed the right
    aggregation granularity up front.
    """

    page_key = models.SlugField(max_length=60, db_index=True)
    page_label = models.CharField(max_length=120)
    visited_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-visited_at"]
