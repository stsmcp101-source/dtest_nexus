from django.contrib.auth.models import Group
from django.db import models


class Role(models.Model):
    """
    A Role is the human-facing wrapper around Django's built-in Group.

    We deliberately reuse Group + Permission (django.contrib.auth) as the
    storage engine for RBAC instead of reinventing it — it is
    battle-tested, works with the admin, and every Django permission
    check (`user.has_perm`) already understands it. Role adds the
    descriptive metadata (description, whether it's a protected system
    role) that the business requires on top of a bare Group name.

    Administrators can create new roles freely (see rule: "Administrator
    ต้องสามารถสร้าง Role ใหม่ได้ด้วย") — creating a Role transparently
    creates its backing Group.
    """

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles (Super Admin, Administrator, ...) cannot be deleted.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            # add/change/delete/view are auto-created by Django already;
            # they map to role.create / role.edit / role.delete / role.view
            # via the registry.
        ]

    def __str__(self):
        return self.name

    @property
    def permissions(self):
        return self.group.permissions.all()

    @property
    def member_count(self):
        return self.group.user_set.count()
