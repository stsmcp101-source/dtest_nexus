from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
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


class DocumentModuleTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(username="docuser", password=self.password)
        grant(
            self.user,
            "document.view", "document.create", "document.edit", "document.delete",
            "document.download", "document.upload",
        )
        self.client.login(username="docuser", password=self.password)

        self.dev = DocumentCategory.objects.create(code="dev", name="Dev", order=1)
        self.mass = DocumentCategory.objects.create(code="mass", name="Mass", order=2)
        self.source = DocumentSource.objects.create(name="Local", provider_type=DocumentSource.ProviderType.LOCAL)

    def _upload(self, code="DEV-ENG-0001", category=None, name="Test Document"):
        f = SimpleUploadedFile(f"{code}.pdf", b"%PDF-1.4 dummy", content_type="application/pdf")
        # follow=True so the one-time success message is consumed on the
        # detail page redirect target, instead of leaking into the next
        # GET (Django's messages framework persists until displayed).
        return self.client.post(reverse("documents:create"), {
            "document_code": code,
            "document_name": name,
            "category": (category or self.dev).pk,
            "source": self.source.pk,
            "status": Document.Status.ACTIVE,
            "file": f,
        }, follow=True)

    def test_create_upload_document(self):
        response = self._upload()
        self.assertEqual(response.status_code, 200)  # followed redirect -> detail page
        self.assertTrue(response.redirect_chain)
        self.assertTrue(Document.objects.filter(document_code="DEV-ENG-0001").exists())

    def test_view_document_detail(self):
        self._upload()
        doc = Document.objects.get(document_code="DEV-ENG-0001")
        response = self.client.get(reverse("documents:detail", args=[doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DEV-ENG-0001")

    def test_download_document(self):
        self._upload()
        doc = Document.objects.get(document_code="DEV-ENG-0001")
        response = self.client.get(reverse("documents:download", args=[doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("Content-Disposition"))

    def test_edit_document(self):
        self._upload()
        doc = Document.objects.get(document_code="DEV-ENG-0001")
        response = self.client.post(reverse("documents:edit", args=[doc.pk]), {
            "document_code": "DEV-ENG-0001",
            "document_name": "Updated Name",
            "category": self.dev.pk,
            "source": self.source.pk,
            "status": Document.Status.ACTIVE,
        })
        self.assertEqual(response.status_code, 302)
        doc.refresh_from_db()
        self.assertEqual(doc.document_name, "Updated Name")

    def test_delete_document(self):
        self._upload()
        doc = Document.objects.get(document_code="DEV-ENG-0001")
        response = self.client.post(reverse("documents:delete", args=[doc.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Document.objects.filter(pk=doc.pk).exists())

    def test_search(self):
        self._upload(code="DEV-ENG-0001", name="Compressor Report")
        self._upload(code="MASS-QA-0001", category=self.mass, name="QA Checklist")
        response = self.client.get(reverse("documents:list"), {"q": "Compressor"})
        self.assertContains(response, "DEV-ENG-0001")
        self.assertNotContains(response, "MASS-QA-0001")

    def test_filter_by_category(self):
        self._upload(code="DEV-ENG-0001")
        self._upload(code="MASS-QA-0001", category=self.mass)
        response = self.client.get(reverse("documents:list"), {"category": "mass"})
        self.assertContains(response, "MASS-QA-0001")
        self.assertNotContains(response, "DEV-ENG-0001")

    def test_pagination(self):
        for i in range(15):
            self._upload(code=f"DEV-ENG-{i:04d}")
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 10)  # DEFAULT_PAGE_SIZE
        response_p2 = self.client.get(reverse("documents:list"), {"page": 2})
        self.assertEqual(len(response_p2.context["page_obj"]), 5)
