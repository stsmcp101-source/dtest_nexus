from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.permissions.registry import resolve


def grant(user, *dotted_codes):
    perms = []
    for code in dotted_codes:
        app_label, codename = resolve(code).split(".")
        perms.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    user.user_permissions.add(*perms)


class UserManagementTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.admin = User.objects.create_user(username="admin_user", password=self.password, is_active=True)
        grant(self.admin, "user.view", "user.create", "user.edit", "user.delete", "user.reset_password")
        self.client.login(username="admin_user", password=self.password)

    def test_create_user(self):
        response = self.client.post(reverse("accounts:user_create"), {
            "username": "newhire",
            "email": "newhire@example.com",
            "first_name": "New",
            "last_name": "Hire",
            "status": User.Status.ACTIVE,
            "is_active": True,
            "roles": [],
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newhire").exists())

    def test_edit_user(self):
        target = User.objects.create_user(username="edituser", password="x")
        response = self.client.post(reverse("accounts:user_edit", args=[target.pk]), {
            "username": "edituser",
            "email": "edited@example.com",
            "first_name": "Edited",
            "last_name": "Name",
            "status": User.Status.ACTIVE,
            "is_active": True,
            "roles": [],
        })
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(target.email, "edited@example.com")

    def test_disable_user(self):
        target = User.objects.create_user(username="disableme", password="x", status=User.Status.ACTIVE)
        response = self.client.post(reverse("accounts:user_toggle_status", args=[target.pk]))
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(target.status, User.Status.DISABLED)
        self.assertFalse(target.is_active)

    def test_role_assignment(self):
        target = User.objects.create_user(username="roletest", password="x")
        group = Group.objects.create(name="TestRole")
        response = self.client.post(reverse("accounts:user_edit", args=[target.pk]), {
            "username": "roletest",
            "email": "roletest@example.com",
            "first_name": "", "last_name": "",
            "status": User.Status.ACTIVE, "is_active": True,
            "roles": [group.pk],
        })
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertIn(group, target.groups.all())

    def test_reset_password(self):
        target = User.objects.create_user(username="pwreset", password="oldpassword")
        old_hash = target.password
        response = self.client.post(reverse("accounts:user_reset_password", args=[target.pk]))
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertNotEqual(target.password, old_hash)
        self.assertTrue(target.must_change_password)
