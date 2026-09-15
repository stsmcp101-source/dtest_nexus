from django.db import models


class MonitoringPlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_monitoringplaceholder", "Can view monitoring module")]
