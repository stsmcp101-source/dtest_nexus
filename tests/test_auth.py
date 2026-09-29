from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(username="testuser", password=self.password)
        self.viewer_group, _ = Group.objects.get_or_create(name="Viewer")

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": self.password}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("dashboard:index"))
        # dashboard.view is not granted by default -> 403, but the
        # session itself must be authenticated (not redirected to login)
        self.assertIn(response.status_code, (200, 403))

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)  # re-renders form with error
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.login(username="testuser", password=self.password)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(response, f"/login/?next=/dashboard/", fetch_redirect_response=False)

    def test_unauthorized_redirects_to_login(self):
        """An anonymous user hitting a login_required view is redirected, not 500'd."""
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_forbidden_for_authenticated_user_without_permission(self):
        self.client.login(username="testuser", password=self.password)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)
