from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable trail of security-relevant and business-relevant events.

    Deliberately denormalised (module/object_type as plain strings)
    rather than a generic FK to keep writes cheap and the table
    queryable even after the referenced object is deleted — an audit
    entry must survive the thing it describes.
    """

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        UPLOAD = "UPLOAD", "Upload"
        DOWNLOAD = "DOWNLOAD", "Download"
        VIEW = "VIEW", "View"
        ROLE_CHANGE = "ROLE_CHANGE", "Role Change"
        PERMISSION_CHANGE = "PERMISSION_CHANGE", "Permission Change"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    username_snapshot = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=30, choices=Action.choices)
    module = models.CharField(max_length=60)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["module"]),
            models.Index(fields=["action"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.username_snapshot} {self.action} {self.module}"

    def save(self, *args, **kwargs):
        if self.user and not self.username_snapshot:
            self.username_snapshot = self.user.get_username()
        super().save(*args, **kwargs)
