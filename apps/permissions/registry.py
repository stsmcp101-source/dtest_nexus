"""
Central permission registry for dtest_nexus.

Every permission in the system is addressed by a short, readable
"dotted code" such as ``document.delete`` or ``user.create`` — this is
what appears in templates, decorators, and the permission matrix UI.

Under the hood, each dotted code maps to a real Django permission
(``app_label.codename``), which is what actually gets stored against
Groups and Users in the database (django.contrib.auth machinery).
Keeping a translation layer here means:

  * The business code never hard-codes a raw Django codename.
  * New permissions can be registered here as the system grows
    (rule #11 — permissions must be extensible) without touching
    every call site.
  * A single source of truth exists for "what permissions exist in
    this system", which powers the Permission Matrix screen.

Extra (non-CRUD) actions such as ``document.download`` are declared as
custom Django permissions in each model's Meta.permissions.
"""

# dotted_code -> "app_label.codename"
PERMISSION_MAP = {
    # Dashboard
    "dashboard.view": "dashboard.view_dashboard",

    # User management
    "user.view": "accounts.view_user",
    "user.create": "accounts.add_user",
    "user.edit": "accounts.change_user",
    "user.delete": "accounts.delete_user",
    "user.reset_password": "accounts.reset_password_user",
    "user.assign_role": "accounts.assign_role_user",

    # Document module
    "document.view": "documents.view_document",
    "document.create": "documents.add_document",
    "document.edit": "documents.change_document",
    "document.delete": "documents.delete_document",
    "document.download": "documents.download_document",
    "document.upload": "documents.upload_document",

    # Reporting
    "report.view": "documents.view_documentreport",
    "report.export": "documents.export_documentreport",

    # Settings
    "settings.view": "core.view_systemsettings",
    "settings.edit": "core.change_systemsettings",

    # Audit
    "audit.view": "audit.view_auditlog",

    # Role / permission administration
    "role.view": "permissions.view_role",
    "role.create": "permissions.add_role",
    "role.edit": "permissions.change_role",
    "role.delete": "permissions.delete_role",

    # Future modules — registered now so navigation / matrix can
    # reference them even before each app grows real business logic.
    "employees.view": "employees.view_employeeplaceholder",
    "certificates.view": "certificates.view_certificateplaceholder",
    "monitoring.view": "monitoring.view_monitoringplaceholder",
    "happy_workplace.view": "happy_workplace.view_happyworkplaceplaceholder",
    "utilities.view": "utilities.view_utilityplaceholder",
}

# Human-readable grouping for the Permission Matrix / Role edit screens.
PERMISSION_GROUPS = {
    "Dashboard": ["dashboard.view"],
    "Users": ["user.view", "user.create", "user.edit", "user.delete", "user.reset_password", "user.assign_role"],
    "Documents": [
        "document.view", "document.create", "document.edit", "document.delete",
        "document.download", "document.upload",
    ],
    "Reports": ["report.view", "report.export"],
    "Settings": ["settings.view", "settings.edit"],
    "Audit": ["audit.view"],
    "Roles & Permissions": ["role.view", "role.create", "role.edit", "role.delete"],
    "Other Modules": [
        "employees.view", "certificates.view", "monitoring.view",
        "happy_workplace.view", "utilities.view",
    ],
}


def resolve(dotted_code):
    """Translate a dotted permission code into a Django 'app_label.codename'."""
    try:
        return PERMISSION_MAP[dotted_code]
    except KeyError as exc:
        raise ValueError(f"Unknown permission code: {dotted_code!r}") from exc


def user_has(user, dotted_code):
    """Check whether `user` holds the permission identified by `dotted_code`."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(resolve(dotted_code))


def user_has_any(user, dotted_codes):
    return any(user_has(user, code) for code in dotted_codes)


def get_registered_permissions_queryset():
    """
    Returns a Django Permission queryset limited to exactly the
    permissions this system knows about (every dotted code in
    PERMISSION_MAP) — used by the user-edit form so an Administrator
    can grant an *individual* user an extra permission (e.g. give one
    specific "User"-role person document.upload) without touching
    their Role, and without being shown Django's unrelated built-in
    permissions (log entries, sessions, etc.).
    """
    from django.contrib.auth.models import Permission
    from django.db.models import Q

    filters = Q()
    for django_code in PERMISSION_MAP.values():
        app_label, codename = django_code.split(".")
        filters |= Q(content_type__app_label=app_label, codename=codename)
    return Permission.objects.filter(filters).select_related("content_type").order_by(
        "content_type__app_label", "codename"
    )
