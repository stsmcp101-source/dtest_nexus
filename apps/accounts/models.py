from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    """Lightweight master data — kept separate so it can be managed via
    Django Admin and reused by other modules (Employees, Documents)."""

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    dtest_nexus's custom user model.

    Extends Django's battle-tested AbstractUser (keeps password hashing,
    permission plumbing, is_staff/is_superuser, etc. exactly as-is) and
    adds the organisational fields the business needs: Employee ID,
    Department, Position, and a soft status flag distinct from
    `is_active` for reporting purposes.

    New fields can be added here in the future without disrupting the
    permission system, since RBAC is handled entirely through Group/
    Permission (see apps.permissions), not through fields on this model.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"
        PENDING = "pending", "Pending"

    employee_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )
    position = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    must_change_password = models.BooleanField(
        default=False, help_text="Forces a password change on next login (e.g. after admin reset)."
    )

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        permissions = [
            ("reset_password_user", "Can reset another user's password"),
            ("assign_role_user", "Can assign a role to a user"),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def role_names(self):
        return list(self.groups.values_list("name", flat=True))

    def is_effectively_active(self):
        return self.is_active and self.status == self.Status.ACTIVE
