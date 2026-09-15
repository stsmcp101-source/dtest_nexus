# dtest_nexus (dTest.nexus)

Enterprise web application for air-conditioning product development &
scalability documentation, built with Python/Django. Starts on SQLite
for development and is designed to move to Microsoft SQL Server / SQL
Express in production without any change to business logic.

---

## 1. Project Overview

dtest_nexus is a modular, permission-controlled internal platform with:

- Custom authentication (login/logout, session security, CSRF)
- Full Role-Based Access Control (RBAC) enforced on the **backend**
- Django Admin as a separate back-office, distinct from the app UI
- A **Document Data** module (search / filter / sort / pagination /
  upload / download, with a storage-provider abstraction ready for
  Google Drive, SharePoint, network drives, or external URLs)
- An audit log recording logins, CRUD, uploads/downloads, and
  role/permission changes
- Five additional modules (Employees, Certificates, Monitoring, Happy
  Workplace, Utilities) scaffolded as real Django apps with working
  permission checks, ready to grow into full modules
- A public marketing Home page and an internal application shell, both
  built from the two supplied HTML references as the design source of
  truth

**Application version:** `1.0.0` (tracked separately from the Django
framework version — see `config/settings/base.py: APP_VERSION`).

---

## 2. Architecture

```
dtest_nexus/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py           # shared settings
│   │   ├── development.py    # SQLite, DEBUG=True
│   │   └── production.py     # SQL Server-ready, DEBUG=False, hardened
│   ├── urls.py                # root URL routing + error handlers
│   ├── wsgi.py / asgi.py
├── apps/
│   ├── core/                  # Home page, SystemSettings, ModuleDefinition, seed command
│   ├── accounts/               # custom User model, login/logout, user management
│   ├── permissions/             # Role model (wraps Group), permission registry, decorators
│   ├── dashboard/               # authenticated landing page
│   ├── audit/                   # AuditLog model + logging service + middleware
│   ├── documents/                # Document Data module (flagship)
│   ├── employees/ certificates/ monitoring/ happy_workplace/ utilities/  # future modules (stubs)
├── templates/
│   ├── base/       (base.html - app shell, public_base.html - marketing shell)
│   ├── components/ (navbar, breadcrumb, page_header, pagination, messages, logo)
│   ├── auth/ dashboard/ documents/ accounts/ permissions/ audit/ core/ placeholder/ errors/
├── static/css/     (design-system.css, home.css, app-shell.css)
├── media/           # uploaded document files (local storage provider)
├── logs/            # application.log, error.log, security.log
├── tests/           # test_auth.py, test_users.py, test_documents.py, test_security.py
├── requirements.txt, requirements/development.txt, requirements/production.txt
├── .env.example, .gitignore
```

### Why Django Group/Permission instead of a custom RBAC table?

`apps.permissions.models.Role` wraps Django's battle-tested
`auth.Group` + `auth.Permission` tables (one-to-one) instead of
reinventing role storage. This means every `user.has_perm(...)` check
Django already knows how to do (including in Django Admin) works
correctly, while `Role` adds the business-facing description/metadata
Django's bare `Group` doesn't have. A central dotted-code registry
(`apps/permissions/registry.py`) maps friendly codes like
`document.delete` to the real `app_label.codename` Django permission,
so views, templates, and the Permission Matrix screen all speak the
same short vocabulary.

---

## 3. Database Model Diagram (textual)

```
User (accounts) ──FK──> Department
User ──M2M──> Group (Django) <──1:1── Role (permissions, adds description/is_system)
Group ──M2M──> Permission (Django)

Document (documents)
 ├─FK─> DocumentCategory (Dev / Mass / ...)
 ├─FK─> DocumentType (Engineering / QA / R&D / Production / ...)
 ├─FK─> DocumentSource (Local / Google Drive / SharePoint / Network / URL)
 ├─FK─> User (created_by, updated_by)
 └─ file (FileField, used when source.provider_type = local)
    external_url (used for non-local providers)

AuditLog (audit)
 └─FK─> User (nullable — survives user deletion via SET_NULL)

ModuleDefinition (core) — drives the Home page module cards and
                           dashboard quick-action tiles
SystemSettings (core) — singleton row, editable via Django Admin
```

---

## 4. Permission Model

Permissions are addressed by short dotted codes, defined in
`apps/permissions/registry.py::PERMISSION_MAP`, e.g.:

```
dashboard.view
user.view / user.create / user.edit / user.delete / user.reset_password / user.assign_role
document.view / document.create / document.edit / document.delete / document.download / document.upload
report.view / report.export
settings.view / settings.edit
audit.view
role.view / role.create / role.edit / role.delete
employees.view / certificates.view / monitoring.view / happy_workplace.view / utilities.view
```

Every protected view is wrapped with:

```python
from apps.permissions.decorators import login_required, require_permission

@login_required
@require_permission("document.delete")
def delete_document(request, pk):
    ...
```

This check happens **on the server**, regardless of whether a menu
item or button is visible in the UI (rule: hiding a link is not
security). Templates use `{% load perms %}{% has_perm "document.edit" as can_edit %}`
only to decide what to *show* — never as the actual gate.

### Seeded roles (Permission Matrix, section 43 of the spec)

| Role | Dashboard | Documents | Users | Reports | Settings |
|---|---|---|---|---|---|
| Super Admin | Full | Full | Full | Full | Full |
| Administrator | Full | Full | Full | Full | Limited (view/edit settings excluded) |
| Manager | View | Full | View | Full | None |
| Engineer | View | Create/Edit | Own | View | None |
| User | View | View | None | View | None |
| Viewer | View | View | None | View | None |

Administrators can create new roles and edit permissions live from
**Role Management** (`/users/roles/`) and inspect the whole grid at
**Permission Matrix** (`/users/permission-matrix/`).

---

## 5. URL Structure (selected)

```
/                              Home (public)
/login/  /logout/              Authentication
/admin/                        Django Admin (back office)
/dashboard/                    Authenticated dashboard
/documents/                    Document Data list
/documents/new/                Upload document
/documents/<id>/               Document detail
/documents/<id>/edit/          Edit document
/documents/<id>/delete/        Delete document
/documents/<id>/open/          Open (redirects to file / external URL)
/documents/<id>/download/      Download
/accounts/users/                User management
/users/roles/                   Role management
/users/permission-matrix/        Permission matrix
/audit/                         Audit log
/employees/ /certificates/ /monitoring/ /happy-workplace/ /utilities/   Future modules (stubs)
```

---

## 6. Installation (Windows)

```powershell
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
REM edit .env and set SECRET_KEY to a real random value

python manage.py migrate
python manage.py seed_initial_data --create-admin
python manage.py runserver 0.0.0.0:8000
```

The seed command prints a one-time admin password to the console —
copy it immediately, it is never stored in plaintext or in source
control.

## Installation (Linux / macOS)

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# edit .env and set SECRET_KEY to a real random value

python manage.py migrate
python manage.py seed_initial_data --create-admin
python manage.py runserver 0.0.0.0:8000
```

---

## 7. Environment Variables

See `.env.example` for the full list. Never commit a real `.env` file.
At minimum, set `SECRET_KEY`. In production, `DATABASE_ENGINE`,
`ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` are required (the app
refuses to start without them — see `config/settings/production.py`).

---

## 8. Database Setup

### SQLite (development, default)
No setup needed beyond `migrate` — the file is created at
`db.sqlite3` in the project root.

### Microsoft SQL Server / SQL Express (production)
1. `pip install mssql-django pyodbc` (or `pip install -r requirements/production.txt`)
2. Install the "ODBC Driver 18 for SQL Server" on the host.
3. Set in `.env`:
   ```
   DATABASE_ENGINE=mssql
   DATABASE_NAME=dtest_nexus
   DATABASE_HOST=SERVER01
   DATABASE_PORT=1433
   DATABASE_USER=...
   DATABASE_PASSWORD=...
   ```
4. Run with `DJANGO_SETTINGS_MODULE=config.settings.production`.
5. `python manage.py migrate` — the same Django ORM migrations apply
   unchanged; no SQLite-specific SQL or field types are used anywhere
   in the codebase (verified per rule #48).

## Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

Never edit `db.sqlite3` directly — all schema changes go through
migrations.

---

## 9. Creating an admin user

Either during seeding:
```bash
python manage.py seed_initial_data --create-admin
```
or the standard Django way:
```bash
python manage.py createsuperuser
```
Superusers can always reach `/admin/` regardless of their assigned
Role/Group permissions.

---

## 10. Running Tests

```bash
python manage.py test
```

Covers: login/logout/unauthorized/forbidden, user CRUD + role
assignment + password reset, the full document lifecycle (create,
upload, view, download, edit, delete, search, filter, pagination),
and a dedicated security suite (unauthorized access, permission
bypass via direct URL, CSRF enforcement).

---

## 11. Static & Media Files

- **Static** (CSS/JS/images shipped with the app): `static/`, served
  from `STATIC_URL` in dev, collected to `staticfiles/` via
  `python manage.py collectstatic` in production (serve via your web
  server / CDN, not Django, in production).
- **Media** (user-uploaded documents): `media/`, served by Django only
  in `DEBUG=True`; serve via your web server / object storage in
  production.

---

## 12. Adding a New Module

1. `python manage.py startapp your_module apps/your_module` (or copy
   the shape of `apps/employees` as a starting point).
2. Add it to `LOCAL_APPS` in `config/settings/base.py`.
3. Give it a placeholder (or real) model with the permissions it needs
   in `Meta.permissions`, register those dotted codes in
   `apps/permissions/registry.py::PERMISSION_MAP` /
   `PERMISSION_GROUPS`.
4. Add `path("your-module/", include((...)))` to `config/urls.py`.
5. Add a `ModuleDefinition` row (via Admin or the seed command) so it
   appears on the Home page and dashboard automatically — no template
   edits required.
6. Extend `templates/components/navbar.html` with a
   `{% if nav.can_view_your_module %}` link if it should appear in the
   top nav.

This mirrors exactly how `employees`, `certificates`, `monitoring`,
`happy_workplace`, and `utilities` were scaffolded in this delivery.

---

## 13. Production Configuration Checklist

- [ ] `DEBUG=False`
- [ ] Real, unique `SECRET_KEY` from the environment
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set to your real domain(s)
- [ ] `DATABASE_ENGINE=mssql` with real credentials (never in source)
- [ ] HTTPS termination in front of Django; `SECURE_SSL_REDIRECT=True`
- [ ] `collectstatic` run and static files served by web server/CDN
- [ ] `logs/` writable by the app process
- [ ] Regular database backups configured at the infrastructure level

---

## 14. Notes on Design Fidelity

- `dtest-nexus (Home).html` → `templates/core/home.html` +
  `static/css/home.css`
- `document-data.html` → `templates/base/base.html` (app shell) +
  `templates/documents/document_list.html` +
  `static/css/app-shell.css`

All colors, fonts, spacing, and component styles were extracted
verbatim into `static/css/design-system.css` (shared tokens),
`home.css`, and `app-shell.css` — no UI was redesigned without
reason, per the project brief.
