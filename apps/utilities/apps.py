from django.apps import AppConfig


class UtilitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.utilities"
    label = "utilities"
    verbose_name = "Tools"

    def ready(self):
        from . import signals  # noqa: F401
