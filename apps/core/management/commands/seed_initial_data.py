"""
python manage.py seed_initial_data

Idempotent seed command (safe to run multiple times) that creates:
  - The six baseline roles from the Permission Matrix (rule #43), wired
    to real permissions via the registry.
  - Document master data: categories (Dev/Mass), a couple of document
    types, and a Local + Google Drive source.
  - The seven homepage/navigation ModuleDefinition rows.
  - A System Settings singleton row.
  - Optionally, one initial administrator account — with a randomly
    generated password printed once to the console, never hard-coded
    in source (rule #41).
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from apps.accounts.models import User
from apps.core.models import ModuleDefinition, SystemSettings
from apps.documents.models import DocumentCategory, DocumentSource, DocumentType
from apps.permissions.models import Role
from apps.permissions.registry import PERMISSION_MAP, resolve

# Role -> list of dotted permission codes it grants.
# Modelled directly on the Permission Matrix in the spec (section 43),
# translated into the concrete permission codes this system defines.
ROLE_PERMISSIONS = {
    "Super Admin": list(PERMISSION_MAP.keys()),  # superuser flag also grants everything
    "Administrator": [
        "dashboard.view",
        "user.view", "user.create", "user.edit", "user.delete", "user.reset_password", "user.assign_role",
        "document.view", "document.create", "document.edit", "document.delete", "document.download", "document.upload",
        "report.view", "report.export",
        "audit.view",
        "role.view", "role.create", "role.edit", "role.delete",
        "employees.view", "certificates.view", "monitoring.view", "happy_workplace.view", "utilities.view",
        # settings.* intentionally omitted -> "Limited" per the matrix
    ],
    # NOTE: "dashboard.view" is deliberately granted only to Super Admin
    # and Administrator below — the Dashboard page is Admin-only per
    # the business requirement "หน้าแดชบอร์ดเข้าได้เฉพาะ Admin". Every
    # other role still gets a normal home via Document Data
    # (see LOGIN_REDIRECT_URL in config/settings/base.py).
    "Manager": [
        "user.view",
        "document.view", "document.create", "document.edit", "document.delete", "document.download", "document.upload",
        "report.view", "report.export",
        "employees.view", "certificates.view", "monitoring.view", "happy_workplace.view", "utilities.view",
    ],
    "Engineer": [
        "document.view", "document.create", "document.edit", "document.download", "document.upload",
        "report.view",
        "employees.view", "certificates.view", "monitoring.view", "happy_workplace.view", "utilities.view",
    ],
    "User": [
        "document.view", "document.download",
        "report.view",
        "employees.view", "certificates.view", "monitoring.view", "happy_workplace.view", "utilities.view",
    ],
    "Viewer": [
        "document.view",
        "report.view",
    ],
}

MODULES = [
    {
        "code": "documents", "name": "Document Data", "short_tag": "DOC", "order": 1,
        "url_name": "documents:list", "is_available": True,
        "description": "จัดเก็บ ค้นหา และติดตามสถานะเอกสารสายงาน Dev และ Mass ได้จากที่เดียว",
        "icon_svg_path": '<path d="M6 2h9l5 5v15H6z"/><path d="M15 2v5h5"/><path d="M9 13h6M9 17h6"/>',
    },
    {
        "code": "employees", "name": "จัดการพนักงาน", "short_tag": "HR", "order": 2,
        "url_name": "employees:index", "is_available": False,
        "description": "ข้อมูลพนักงาน การลา และประวัติการทำงานครบถ้วนในระบบเดียว",
        "icon_svg_path": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.2c2.3.3 4.5 1.9 4.5 4.8"/>',
    },
    {
        "code": "certificates", "name": "Certificate", "short_tag": "CERT", "order": 3,
        "url_name": "certificates:index", "is_available": False,
        "description": "ออก ต่ออายุ และติดตามใบรับรองหรือวุฒิบัตรของพนักงานทุกคน",
        "icon_svg_path": '<rect x="4" y="4" width="16" height="12" rx="1.5"/><path d="M9 20l3-2 3 2"/><circle cx="12" cy="9" r="2.4"/>',
    },
    {
        "code": "monitoring", "name": "Monitoring & Dashboard", "short_tag": "MON", "order": 4,
        "url_name": "monitoring:index", "is_available": False,
        "description": "ภาพรวมข้อมูลและตัวชี้วัดสำคัญขององค์กรแบบเรียลไทม์",
        "icon_svg_path": '<path d="M4 20V10M11 20V4M18 20v-7"/>',
    },
    {
        "code": "happy-workplace", "name": "Happy Workplace", "short_tag": "HWP", "order": 5,
        "url_name": "happy_workplace:index", "is_available": False,
        "description": "กิจกรรม สวัสดิการ และความเป็นอยู่ที่ดีของพนักงานในองค์กร",
        "icon_svg_path": '<path d="M12 21s-7-4.4-9.3-8.8C1 8.6 3 5 6.5 5c1.9 0 3.3 1 3.5 2.6C10.2 6 11.6 5 13.5 5 17 5 19 8.6 17.3 12.2 15 16.6 12 21 12 21z"/>',
    },
    {
        "code": "utilities", "name": "Utilities", "short_tag": "UTIL", "order": 6,
        "url_name": "utilities:index", "is_available": False,
        "description": "เครื่องมือช่วยงานประจำวัน เช่น แบบฟอร์มกลางและตัวช่วยคำนวณ",
        "icon_svg_path": '<path d="M14.7 6.3a3 3 0 00-4.2 4.2L4 17v3h3l6.5-6.5a3 3 0 004.2-4.2l-2.3 2.3-2-2z"/>',
    },
    {
        "code": "other", "name": "อื่นๆ", "short_tag": "OTHER", "order": 7,
        "url_name": "", "is_available": False,
        "description": "ฟังก์ชันเพิ่มเติมและโมดูลใหม่ที่กำลังจะเปิดให้ใช้งานเร็ว ๆ นี้",
        "icon_svg_path": '<circle cx="6" cy="6" r="1.6"/><circle cx="12" cy="6" r="1.6"/><circle cx="18" cy="6" r="1.6"/><circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/><circle cx="6" cy="18" r="1.6"/><circle cx="12" cy="18" r="1.6"/><circle cx="18" cy="18" r="1.6"/>',
    },
]


class Command(BaseCommand):
    help = "Seed initial roles, permissions, master data, modules, and (optionally) an admin user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-admin", action="store_true",
            help="Also create an initial administrator account if none exists.",
        )
        parser.add_argument("--admin-username", default="admin")
        parser.add_argument("--admin-email", default="admin@dtest.local")

    def handle(self, *args, **options):
        self.seed_roles()
        self.seed_document_master_data()
        self.seed_modules()
        SystemSettings.get_solo()
        self.stdout.write(self.style.SUCCESS("System settings singleton ensured."))

        if options["create_admin"]:
            self.seed_admin(options["admin_username"], options["admin_email"])

        self.stdout.write(self.style.SUCCESS("Initial data seed complete."))

    def seed_roles(self):
        for role_name, codes in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            role, created = Role.objects.get_or_create(
                group=group, defaults={"name": role_name, "is_system": True}
            )
            if not created:
                role.is_system = True
                role.save(update_fields=["is_system"])

            perms = []
            for code in codes:
                try:
                    app_label, codename = resolve(code).split(".")
                except (ValueError, KeyError):
                    continue
                try:
                    perms.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"Permission {app_label}.{codename} (code '{code}') not found - "
                        "did you run migrate first?"
                    ))
            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"Role '{role_name}' -> {len(perms)} permissions."))

    def seed_document_master_data(self):
        dev, _ = DocumentCategory.objects.get_or_create(code="dev", defaults={"name": "Dev", "order": 1})
        mass, _ = DocumentCategory.objects.get_or_create(code="mass", defaults={"name": "Mass", "order": 2})

        for code, name in [("eng", "Engineering"), ("qa", "Quality Assurance"), ("rnd", "R&D"), ("prd", "Production")]:
            DocumentType.objects.get_or_create(code=code, defaults={"name": name})

        DocumentSource.objects.get_or_create(
            name="Local Disk", defaults={"provider_type": DocumentSource.ProviderType.LOCAL}
        )
        DocumentSource.objects.get_or_create(
            name="Google Drive", defaults={"provider_type": DocumentSource.ProviderType.GOOGLE_DRIVE}
        )
        DocumentSource.objects.get_or_create(
            name="SharePoint", defaults={"provider_type": DocumentSource.ProviderType.SHAREPOINT}
        )
        DocumentSource.objects.get_or_create(
            name="Network Drive", defaults={"provider_type": DocumentSource.ProviderType.NETWORK_DRIVE}
        )
        DocumentSource.objects.get_or_create(
            name="External URL", defaults={"provider_type": DocumentSource.ProviderType.EXTERNAL_URL}
        )
        self.stdout.write(self.style.SUCCESS("Document master data (categories/types/sources) ensured."))

    def seed_modules(self):
        for m in MODULES:
            ModuleDefinition.objects.update_or_create(code=m["code"], defaults=m)
        self.stdout.write(self.style.SUCCESS(f"{len(MODULES)} module definitions ensured."))

    def seed_admin(self, username, email):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING("A superuser already exists; skipping admin creation."))
            return

        temp_password = get_random_string(16)
        admin = User.objects.create_superuser(username=username, email=email, password=temp_password)
        super_admin_group = Group.objects.filter(name="Super Admin").first()
        if super_admin_group:
            admin.groups.add(super_admin_group)

        self.stdout.write(self.style.SUCCESS(
            f"\nInitial administrator created:\n"
            f"  username: {username}\n"
            f"  password: {temp_password}\n"
            f"  (This password is shown once. Change it immediately after logging in.)\n"
        ))
