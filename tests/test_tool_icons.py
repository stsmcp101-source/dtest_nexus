import json
import tempfile
from pathlib import Path

from django.db import connection, transaction
from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from apps.utilities.icon_memory import remember_icon, tool_icon_urls
from apps.utilities.models import ToolIcon


class ToolIconMemoryTests(TransactionTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.directory.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.name = "tools/icons/saved.png"
        path = Path(self.directory.name) / self.name
        path.parent.mkdir(parents=True)
        path.write_bytes(b"saved image")

    def test_saved_logo_survives_missing_database_record(self):
        icon = ToolIcon.objects.create(key="pdf_edit", image=self.name)
        # Simulate restoring an older DB without sending intentional-reset signals.
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM utilities_toolicon WHERE id = %s", [icon.pk])
        self.assertEqual(tool_icon_urls()["pdf_edit"], "/media/" + self.name)
        response = self.client.get(reverse("utilities:index"))
        self.assertContains(response, '/media/' + self.name)

    def test_reset_does_not_restore_old_logo(self):
        icon = ToolIcon.objects.create(key="pdf_edit", image=self.name)
        icon.delete()
        self.assertNotIn("pdf_edit", tool_icon_urls())
        self.assertTrue((Path(self.directory.name) / self.name).exists())

    def test_replacement_is_remembered(self):
        icon = ToolIcon.objects.create(key="pdf_edit", image=self.name)
        replacement = "tools/icons/new.png"
        (Path(self.directory.name) / replacement).write_bytes(b"new image")
        icon.image = replacement
        icon.save()
        record = Path(self.directory.name) / "tools/icon-memory/pdf_edit.json"
        self.assertEqual(json.loads(record.read_text())["image"], replacement)

    def test_rollback_preserves_previous_memory(self):
        icon = ToolIcon.objects.create(key="pdf_edit", image=self.name)
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                icon.image = "tools/icons/rolled-back.png"
                icon.save()
                raise RuntimeError("cancel")
        self.assertEqual(tool_icon_urls()["pdf_edit"], "/media/" + self.name)

    def test_missing_file_and_invalid_memory_do_not_break_page(self):
        remember_icon("pdf_edit", "tools/icons/missing.png")
        remember_icon("qr_code", "../outside.png")
        self.assertEqual(tool_icon_urls(), {})
        self.assertEqual(self.client.get(reverse("utilities:index")).status_code, 200)
