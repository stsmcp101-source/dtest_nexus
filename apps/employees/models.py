from django.db import models


class EmployeePlaceholder(models.Model):
    """
    Placeholder anchor for the `employees.view` permission until this
    module's real business logic (Employee, Leave, etc.) is built out.
    Keeping it as its own Django app now — rather than bolting Employee
    models onto another app later — means turning this into a full
    module never requires restructuring (rule #36).
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_employeeplaceholder", "Can view employees module")]
