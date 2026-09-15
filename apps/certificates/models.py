from django.db import models


class CertificatePlaceholder(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_certificateplaceholder", "Can view certificates module")]
