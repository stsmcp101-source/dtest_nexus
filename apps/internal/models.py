from django.db import models


class InternalPlaceholder(models.Model):
    """
    Placeholder anchor for the `internal.view` permission — a
    login-and-permission-gated internal/testing-only page, not linked
    from the Home page module grid or the app nav.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_internalplaceholder", "Can view internal module")]


class InternalIcon(models.Model):
    key = models.SlugField(max_length=40, unique=True)
    image = models.ImageField(upload_to="internal/icons/")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
