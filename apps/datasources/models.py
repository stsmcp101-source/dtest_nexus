from django.conf import settings
from django.db import models

from . import crypto


class DatabaseConnection(models.Model):
    """
    An admin-registered external SQL Server connection (Production,
    Employee, Test Room, ...) that the Data Explorer can browse read-only
    alongside the app's own SQLite database. The app's own DATABASES
    setting is untouched by this model — it stays whatever
    config/settings/*.py says (SQLite in development).
    """

    name = models.CharField(max_length=100, unique=True, help_text="e.g. Production, Employee, Test Room")
    server = models.CharField(max_length=255, help_text="Host or host\\instance, e.g. 192.168.1.100")
    port = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for the driver default (1433)")
    database_name = models.CharField(max_length=200)
    username = models.CharField(max_length=150, blank=True)
    encrypted_password = models.TextField(blank=True)
    driver = models.CharField(max_length=100, default="ODBC Driver 18 for SQL Server")
    is_active = models.BooleanField(default=True, help_text="Inactive connections are hidden from Data Explorer")

    last_test_ok = models.BooleanField(null=True, blank=True)
    last_test_at = models.DateTimeField(null=True, blank=True)
    last_test_message = models.CharField(max_length=500, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_password(self, raw_password):
        self.encrypted_password = crypto.encrypt(raw_password)

    def get_password(self):
        return crypto.decrypt(self.encrypted_password)
