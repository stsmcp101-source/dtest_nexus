"""
Root URL configuration for dtest_nexus.

Each Django app owns its own urls.py; this file only wires them together
under their namespaces, and adds the API v1 placeholder mount point so
that a REST API can be introduced later without restructuring anything.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts.forms import StyledAuthenticationForm
from apps.accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Root-level aliases required by spec section 8 (AUTHENTICATION):
    # canonical URLs are /login/ and /logout/. The namespaced
    # accounts:login / accounts:logout routes below point at the same
    # views and exist so other apps can `{% url 'accounts:login' %}`.
    path("login/", accounts_views.StyledLoginView.as_view(authentication_form=StyledAuthenticationForm), name="login"),
    path("logout/", accounts_views.logout_view, name="logout"),

    path("", include(("apps.core.urls", "core"), namespace="core")),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("dashboard/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),
    path("documents/", include(("apps.documents.urls", "documents"), namespace="documents")),
    path("employees/", include(("apps.employees.urls", "employees"), namespace="employees")),
    path("certificates/", include(("apps.certificates.urls", "certificates"), namespace="certificates")),
    path("monitoring/", include(("apps.monitoring.urls", "monitoring"), namespace="monitoring")),
    path("happy-workplace/", include(("apps.happy_workplace.urls", "happy_workplace"), namespace="happy_workplace")),
    path("utilities/", include(("apps.utilities.urls", "utilities"), namespace="utilities")),
    path("audit/", include(("apps.audit.urls", "audit"), namespace="audit")),
    path("users/", include(("apps.permissions.urls", "permissions"), namespace="permissions")),

    # Reserved mount point for a future DRF-based API. Adding
    # apps.api.urls later requires no change to this structure.
    # path("api/v1/", include(("apps.api.urls", "api"), namespace="api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "apps.core.views.error_400"
handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
