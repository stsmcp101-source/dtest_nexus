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
    "happy_workplace.edit": "happy_workplace.change_announcement",
    "utilities.view": "utilities.view_utilityplaceholder",

    # Data Explorer — browsing external SQL Server connections is more
    # sensitive than the other "Other Modules" stubs above, so it's its
    # own code rather than folded into utilities.view. Managing the
    # connections themselves (adding credentials) reuses settings.edit
    # instead of a separate code, same as the other Settings sub-pages.
    "datasource.view": "datasources.view_databaseconnection",

    # Internal/testing-only page — deliberately not granted to any
    # seeded role except Super Admin (see seed_initial_data.py).
    "internal.view": "internal.view_internalplaceholder",

    # Spare Parts — one of the Internal section's sub-tools. Viewing the
    # page reuses internal.view (the whole Internal section is already
    # Super-Admin-only); this extra code gates the actual stock
    # transactions/import, same split as datasource.view vs settings.edit.
    "internal.spare_part_edit": "spare_parts.change_sparepart",

    # External Training History — another Internal sub-tool, same split
    # (viewing reuses internal.view, adding/editing records gets its own code).
    "internal.training_edit": "training_history.change_trainingemployee",
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
        "happy_workplace.view", "happy_workplace.edit", "utilities.view",
    ],
    "Data Explorer": ["datasource.view"],
    "Internal": ["internal.view", "internal.spare_part_edit", "internal.training_edit"],
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


def grouped_permission_checkboxes(bound_field):
    """
    Buckets a CheckboxSelectMultiple-rendered ModelMultipleChoiceField's
    subwidgets (e.g. UserForm.extra_permissions) by PERMISSION_GROUPS
    section — turns one long flat checkbox list into scannable,
    labelled sections matching the Permission Matrix screen's grouping.

    Each subwidget is paired with the queryset item at the same index
    (CheckboxSelectMultiple always renders in queryset order), then
    looked up by (app_label, codename) back to its dotted code.
    Permissions with no registered dotted code, and empty sections,
    are silently skipped.
    """
    reverse_map = {v: k for k, v in PERMISSION_MAP.items()}
    queryset = bound_field.field.queryset
    by_code = {}
    for checkbox, perm in zip(bound_field, queryset):
        dotted = reverse_map.get(f"{perm.content_type.app_label}.{perm.codename}")
        if dotted:
            by_code[dotted] = checkbox

    groups = []
    for label, codes in PERMISSION_GROUPS.items():
        checkboxes = [by_code[code] for code in codes if code in by_code]
        if checkboxes:
            groups.append({"label": label, "checkboxes": checkboxes})
    return groups


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
