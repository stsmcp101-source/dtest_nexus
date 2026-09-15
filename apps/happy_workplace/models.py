from django.db import models


class HappyWorkplacePlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_happyworkplaceplaceholder", "Can view happy workplace module")]
