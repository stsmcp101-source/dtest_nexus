from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.documents.models import Document, DocumentCategory, DocumentSource
from apps.permissions.registry import resolve


def grant(user, *dotted_codes):
    perms = []
    for code in dotted_codes:
        app_label, codename = resolve(code).split(".")
        perms.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    user.user_permissions.add(*perms)


class SecurityTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.category = DocumentCategory.objects.create(code="dev", name="Dev")
        self.source = DocumentSource.objects.create(name="Local", provider_type=DocumentSource.ProviderType.LOCAL)

        self.full_user = User.objects.create_user(username="fulluser", password=self.password)
        grant(
            self.full_user, "document.view", "document.create", "document.edit",
            "document.delete", "document.download", "document.upload",
        )
        c = Client()
        c.login(username="fulluser", password=self.password)
        f = SimpleUploadedFile("secret.pdf", b"%PDF-1.4", content_type="application/pdf")
        c.post(reverse("documents:create"), {
            "document_code": "DEV-ENG-SECRET",
            "document_name": "Secret Document",
            "category": self.category.pk,
            "source": self.source.pk,
            "status": Document.Status.ACTIVE,
            "file": f,
        })
        self.document = Document.objects.get(document_code="DEV-ENG-SECRET")

        # A user with only view permission, deliberately missing delete/edit/upload.
        self.limited_user = User.objects.create_user(username="limiteduser", password=self.password)
        grant(self.limited_user, "document.view")

    def test_document_list_is_public(self):
        """Document Data viewing is intentionally public (no login
        required) per the business requirement — but write actions on
        the same module must still require both login and permission."""
        c = Client()
        response = c.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)

        response = c.get(reverse("documents:detail", args=[self.document.pk]))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_access_redirects_anonymous_for_gated_actions(self):
        c = Client()
        response = c.get(reverse("documents:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        response = c.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_dashboard_is_admin_only(self):
        """A user with a non-admin role (e.g. 'User') must get 403 on
        the dashboard, even when fully authenticated."""
        from django.contrib.auth.models import Group

        non_admin = User.objects.create_user(username="rank_and_file", password=self.password)
        user_role, _ = Group.objects.get_or_create(name="User")
        non_admin.groups.add(user_role)

        c = Client()
        c.login(username="rank_and_file", password=self.password)
        response = c.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 403)

    def test_permission_bypass_direct_url_delete(self):
        """A user without document.delete cannot delete by hitting the URL directly,
        even though the UI would never render the delete button for them."""
        c = Client()
        c.login(username="limiteduser", password=self.password)

        response = c.get(reverse("documents:delete", args=[self.document.pk]))
        self.assertEqual(response.status_code, 403)

        response = c.post(reverse("documents:delete", args=[self.document.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())

    def test_permission_bypass_direct_url_edit(self):
        c = Client()
        c.login(username="limiteduser", password=self.password)
        response = c.post(reverse("documents:edit", args=[self.document.pk]), {
            "document_name": "Hacked Name",
        })
        self.assertEqual(response.status_code, 403)
        self.document.refresh_from_db()
        self.assertNotEqual(self.document.document_name, "Hacked Name")

    def test_permission_bypass_direct_url_upload(self):
        c = Client()
        c.login(username="limiteduser", password=self.password)
        f = SimpleUploadedFile("hack.pdf", b"%PDF-1.4", content_type="application/pdf")
        response = c.post(reverse("documents:create"), {
            "document_code": "HACK-0001",
            "document_name": "Should not be created",
            "category": self.category.pk,
            "source": self.source.pk,
            "status": Document.Status.ACTIVE,
            "file": f,
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Document.objects.filter(document_code="HACK-0001").exists())

    def test_csrf_protection_enforced(self):
        """A POST without a valid CSRF token must be rejected."""
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="fulluser", password=self.password)
        response = csrf_client.post(reverse("documents:delete", args=[self.document.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())

    def test_user_management_forbidden_without_permission(self):
        c = Client()
        c.login(username="limiteduser", password=self.password)
        response = c.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_role_management_forbidden_without_permission(self):
        c = Client()
        c.login(username="limiteduser", password=self.password)
        response = c.get(reverse("permissions:role_list"))
        self.assertEqual(response.status_code, 403)
