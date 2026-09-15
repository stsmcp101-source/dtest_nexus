from django.db import models


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
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text="False = 'coming soon' styling on the home page")

    class Meta:
        ordering = ["order", "code"]

    def __str__(self):
        return self.name
