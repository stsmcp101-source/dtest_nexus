"""
Exposes a `can(code)` helper and a precomputed `nav_perms` dict to every
template, so the navbar/sidebar can decide what to *show* based on the
signed-in user's permissions.

IMPORTANT: this only controls visibility (rule #13 — hiding a menu item
is a UX nicety, not security). The actual enforcement happens in
apps.permissions.decorators.require_permission on the view itself.
"""
from .registry import PERMISSION_MAP, user_has


class _PermChecker:
    """Callable + dict-like helper usable as {{ can.document.view }} isn't
    valid Django template syntax for dotted codes with a dot in the key,
    so templates call it as a function: {% if can("document.view") %}
    is not valid Django template syntax either — Django templates can
    only call zero-argument callables directly. We therefore expose a
    custom template tag (see templatetags/perms.py) for the general
    case, and pre-compute the common nav flags below for simple cases.
    """

    def __init__(self, user):
        self.user = user

    def __call__(self, code):
        return user_has(self.user, code)


def nav_permissions(request):
    user = getattr(request, "user", None)
    checker = _PermChecker(user)
    nav_flags = {
        "can_view_dashboard": checker("dashboard.view"),
        # Document Data is a public, view-anywhere module (no login
        # required — see apps.documents.views.document_list), so its
        # nav link is always shown, including to anonymous visitors.
        # Upload/Edit/Delete buttons inside that page still check the
        # real document.upload/edit/delete permissions individually.
        "can_view_documents": True,
        "can_view_users": checker("user.view"),
        "can_view_roles": checker("role.view"),
        "can_view_audit": checker("audit.view"),
        "can_view_settings": checker("settings.view"),
        "can_view_employees": checker("employees.view"),
        "can_view_certificates": checker("certificates.view"),
        "can_view_monitoring": checker("monitoring.view"),
        "can_view_happy_workplace": checker("happy_workplace.view"),
        "can_view_utilities": checker("utilities.view"),
    }
    return {
        "can": checker,
        "nav": nav_flags,
        "all_permission_codes": list(PERMISSION_MAP.keys()),
    }
