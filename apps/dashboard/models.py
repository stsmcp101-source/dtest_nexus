from django.db import models


class DashboardAccess(models.Model):
    """
    Django's permission system is model-anchored: every permission
    belongs to a content type. The Dashboard has no data of its own to
    persist, but it still needs a `dashboard.view` permission, so this
    zero-row marker model exists purely to own that permission
    (`view_dashboardaccess` -> registry code `dashboard.view`).
    """

    class Meta:
        managed = False  # no table needed; Django still creates the permission
        default_permissions = ()
        permissions = [("view_dashboard", "Can view dashboard")]
