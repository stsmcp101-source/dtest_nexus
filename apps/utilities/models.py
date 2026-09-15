from django.db import models


class UtilityPlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_utilityplaceholder", "Can view utilities module")]
