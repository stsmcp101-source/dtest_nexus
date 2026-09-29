from django.db import models


class UtilityPlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_utilityplaceholder", "Can view tools module")]


class ToolIcon(models.Model):
    """Admin-uploaded logo replacing one Tools hub tile's default line icon.
    `key` is a tile key from apps.utilities.tool_icons.TOOL_ICONS; no row
    means the tile shows its default icon."""

    key = models.SlugField(max_length=40, unique=True)
    image = models.ImageField(upload_to="tools/icons/")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
