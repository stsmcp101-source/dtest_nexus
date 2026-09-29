import io
import tempfile
from pathlib import Path
from PIL import Image
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.urls import reverse
from apps.accounts.models import User
from apps.internal.models import InternalIcon
from apps.internal.icon_memory import internal_icon_urls

class InternalIconTests(TransactionTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.admin = User.objects.create_superuser(username='iconadmin', password='test-pass')
        self.user = User.objects.create_user(username='viewer')
        self.user.user_permissions.add(Permission.objects.get(codename='view_internalplaceholder'))
        self.url = reverse('internal:icon_settings')

    def upload(self, name='logo.png'):
        data = io.BytesIO()
        Image.new('RGB', (20,20), 'blue').save(data, 'PNG')
        return SimpleUploadedFile(name, data.getvalue(), content_type='image/png')

    def test_access_and_hidden_button(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'icon_spare_parts':self.upload()}).status_code, 403)
        self.assertFalse(InternalIcon.objects.exists())
        self.assertNotContains(self.client.get(reverse('internal:index')), 'ตั้งค่าโลโก้')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('internal:index')), 'ตั้งค่าโลโก้')
        self.assertContains(self.client.get(self.url), 'type="file"', count=9)

    def test_upload_replace_recovery_reset(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url, {'icon_spare_parts':self.upload()}).status_code,302)
        first = InternalIcon.objects.get(key='spare_parts').image.name
        self.assertEqual(self.client.post(self.url, {'icon_spare_parts':self.upload()}).status_code,302)
        icon = InternalIcon.objects.get(key='spare_parts')
        self.assertNotEqual(first,icon.image.name)
        self.assertTrue((Path(self.tmp.name)/first).exists())
        self.assertContains(self.client.get(reverse('internal:index')), icon.image.url)
        with connection.cursor() as c:
            c.execute('DELETE FROM internal_internalicon WHERE id=%s',[icon.pk])
        self.assertEqual(internal_icon_urls()['spare_parts'],icon.image.url)
        self.assertEqual(self.client.post(self.url, {'reset_spare_parts':'on'}).status_code,302)
        self.assertNotIn('spare_parts',internal_icon_urls())

    def test_reject_invalid_upload(self):
        self.client.force_login(self.admin)
        response=self.client.post(self.url,{'icon_spare_parts':SimpleUploadedFile('bad.svg',b'<svg/>')})
        self.assertEqual(response.status_code,200)
        self.assertFalse(InternalIcon.objects.exists())
