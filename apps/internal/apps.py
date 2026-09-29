from django.apps import AppConfig


class InternalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.internal"
    label = "internal"
    verbose_name = "Internal"

    def ready(self):
        from . import signals  # noqa: F401
