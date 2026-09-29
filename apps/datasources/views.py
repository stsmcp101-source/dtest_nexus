from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.permissions.decorators import require_permission
from apps.permissions.registry import user_has

from . import db_utils, env_utils
from .db_utils import QueryError
from .forms import DatabaseConnectionForm, PrimaryDatabaseSettingsForm
from .models import DatabaseConnection

# ---------------------------------------------------------------------------
# Data Explorer and Database Connections share one page (templates/datasources/index.html,
# tabbed) to save top-nav space. Explorer is gated by the broader datasource.view;
# Connections management stays Super-Admin-only (settings.edit) — its tab is simply
# hidden for users who lack that permission (the CRUD views below keep their own
# real @require_permission gate regardless, per rule #13: hiding a tab isn't security).
# ---------------------------------------------------------------------------

def _current_primary_db():
    """Read-only summary of the database this process is actually
    connected to right now (never the password)."""
    db = django_settings.DATABASES.get("default", {})
    engine_path = db.get("ENGINE", "")
    if "sqlite3" in engine_path:
        return {"engine_label": "SQLite", "target": str(db.get("NAME", ""))}
    if "mssql" in engine_path:
        host, port, name = db.get("HOST", ""), db.get("PORT", ""), db.get("NAME", "")
        server = f"{host}:{port}" if port else host
        return {"engine_label": "Microsoft SQL Server", "target": f"{server} / {name}"}
    return {"engine_label": engine_path or "ไม่ทราบ", "target": str(db.get("NAME", ""))}


def _primary_db_management_context():
    env_values = env_utils.read_database_env()
    initial = {
        "engine": env_values.get("DATABASE_ENGINE") or "sqlite",
        "name": env_values.get("DATABASE_NAME") or "",
        "host": env_values.get("DATABASE_HOST") or "",
        "port": env_values.get("DATABASE_PORT") or "",
        "user": env_values.get("DATABASE_USER") or "",
        "odbc_driver": env_values.get("DATABASE_ODBC_DRIVER") or "",
    }
    return {
        "current_db": _current_primary_db(),
        "primary_db_form": PrimaryDatabaseSettingsForm(initial=initial),
    }


@login_required
@require_permission("settings.edit")
def connection_list(request):
    context = {
        "initial_tab": "connections",
        "can_manage_connections": True,
        "explorer_connections": DatabaseConnection.objects.filter(is_active=True),
        "all_connections": DatabaseConnection.objects.all(),
    }
    context.update(_primary_db_management_context())
    return render(request, "datasources/index.html", context)


@login_required
@require_permission("settings.edit")
def connection_create(request):
    if request.method == "POST":
        form = DatabaseConnectionForm(request.POST)
        if form.is_valid():
            conn = form.save(commit=False)
            conn.created_by = request.user
            conn.save()
            log_action(
                user=request.user, action="CREATE", module="datasources", object_type="DatabaseConnection",
                object_id=conn.pk, description=f"สร้างการเชื่อมต่อฐานข้อมูล '{conn.name}'",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"เพิ่มการเชื่อมต่อ '{conn.name}' เรียบร้อยแล้ว")
            return redirect("datasources:connection_list")
    else:
        form = DatabaseConnectionForm()
    return render(request, "datasources/connection_form.html", {"form": form, "mode": "create"})


@login_required
@require_permission("settings.edit")
def connection_edit(request, pk):
    conn = get_object_or_404(DatabaseConnection, pk=pk)
    if request.method == "POST":
        form = DatabaseConnectionForm(request.POST, instance=conn)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user, action="UPDATE", module="datasources", object_type="DatabaseConnection",
                object_id=conn.pk, description=f"แก้ไขการเชื่อมต่อฐานข้อมูล '{conn.name}'",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"บันทึกการเชื่อมต่อ '{conn.name}' แล้ว")
            return redirect("datasources:connection_list")
    else:
        form = DatabaseConnectionForm(instance=conn)
    return render(request, "datasources/connection_form.html", {"form": form, "mode": "edit", "connection": conn})


@login_required
@require_permission("settings.edit")
def connection_delete(request, pk):
    conn = get_object_or_404(DatabaseConnection, pk=pk)
    if request.method == "POST":
        name = conn.name
        conn.delete()
        log_action(
            user=request.user, action="DELETE", module="datasources", object_type="DatabaseConnection",
            object_id=pk, description=f"ลบการเชื่อมต่อฐานข้อมูล '{name}'",
            ip_address=get_client_ip(request),
        )
        messages.success(request, f"ลบการเชื่อมต่อ '{name}' แล้ว")
        return redirect("datasources:connection_list")
    return render(request, "datasources/connection_confirm_delete.html", {"connection": conn})


@login_required
@require_permission("settings.edit")
def connection_test(request):
    """AJAX endpoint backing the "Test Connection" button. Tests whatever
    is currently typed in the form (works before the row is even saved);
    if editing an existing connection and the password field was left
    blank, falls back to that connection's already-stored password so
    "test without retyping the password" works too."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed"}, status=405)

    pk = request.POST.get("pk")
    password = request.POST.get("password", "")
    if not password and pk:
        existing = DatabaseConnection.objects.filter(pk=pk).first()
        if existing:
            password = existing.get_password()

    port_raw = request.POST.get("port", "").strip()
    ok, message = db_utils.test_connection(
        server=request.POST.get("server", "").strip(),
        database=request.POST.get("database_name", "").strip(),
        username=request.POST.get("username", "").strip(),
        password=password,
        driver=request.POST.get("driver", "").strip() or "ODBC Driver 18 for SQL Server",
        port=int(port_raw) if port_raw.isdigit() else None,
    )

    if pk:
        conn = DatabaseConnection.objects.filter(pk=pk).first()
        if conn:
            db_utils.record_test_result(conn, ok, message)

    log_action(
        user=request.user, action="VIEW", module="datasources", object_type="DatabaseConnection",
        object_id=pk or "", description=f"ทดสอบการเชื่อมต่อฐานข้อมูล — {'สำเร็จ' if ok else 'ไม่สำเร็จ'}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": ok, "message": message})


# ---------------------------------------------------------------------------
# Data Explorer — browse read-only data from any registered connection
# (or the app's own SQLite database), gated by the broader datasource.view
# permission rather than settings.edit.
# ---------------------------------------------------------------------------

@login_required
@require_permission("datasource.view")
def browse_index(request):
    can_manage_connections = user_has(request.user, "settings.edit")
    context = {
        "initial_tab": "explorer",
        "can_manage_connections": can_manage_connections,
        "explorer_connections": DatabaseConnection.objects.filter(is_active=True),
    }
    if can_manage_connections:
        context["all_connections"] = DatabaseConnection.objects.all()
        context.update(_primary_db_management_context())
    return render(request, "datasources/index.html", context)


@login_required
@require_permission("datasource.view")
def browse_tables(request):
    source = request.GET.get("source", "")
    conn_row = None
    if source != "sqlite":
        conn_row = get_object_or_404(DatabaseConnection, pk=source, is_active=True)
    try:
        tables = db_utils.list_tables("sqlite" if source == "sqlite" else "mssql", conn_row)
    except QueryError as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=400)
    return JsonResponse({"ok": True, "tables": tables})


@login_required
@require_permission("datasource.view")
def browse_data(request):
    source = request.GET.get("source", "")
    table = request.GET.get("table", "")
    if not table:
        return JsonResponse({"ok": False, "message": "กรุณาเลือกตาราง"}, status=400)

    conn_row = None
    if source != "sqlite":
        conn_row = get_object_or_404(DatabaseConnection, pk=source, is_active=True)

    try:
        result = db_utils.load_table("sqlite" if source == "sqlite" else "mssql", table, conn_row)
    except QueryError as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=400)

    log_action(
        user=request.user, action="VIEW", module="datasources", object_type="Table",
        object_id=table, description=f"เปิดดูตาราง '{table}' จาก {conn_row.name if conn_row else 'SQLite'}",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"ok": True, **result})


# ---------------------------------------------------------------------------
# Primary database settings — where THIS APP'S OWN data (not an external
# Data Explorer connection) lives. Super-Admin-only. Writes to .env, not the
# database, and never touches the running process's connection: Django reads
# DATABASES once at boot, so this only takes effect after a manual restart,
# and never moves any existing data on its own — see PrimaryDatabaseSettingsForm.
# ---------------------------------------------------------------------------

@login_required
@require_permission("settings.edit")
def primary_database_settings_update(request):
    if request.method == "POST":
        form = PrimaryDatabaseSettingsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            updates = {"DATABASE_ENGINE": data["engine"], "DATABASE_NAME": data["name"]}
            if data["engine"] == "mssql":
                updates["DATABASE_HOST"] = data.get("host", "")
                updates["DATABASE_PORT"] = data.get("port", "")
                updates["DATABASE_USER"] = data.get("user", "")
                updates["DATABASE_ODBC_DRIVER"] = data.get("odbc_driver") or "ODBC Driver 18 for SQL Server"
                if data.get("password"):
                    updates["DATABASE_PASSWORD"] = data["password"]
            env_utils.write_database_env(updates)
            log_action(
                user=request.user, action="UPDATE", module="datasources", object_type="PrimaryDatabase",
                description=(
                    f"อัปเดตการตั้งค่าฐานข้อมูลหลักใน .env เป็น engine={data['engine']} "
                    "(ยังไม่มีผลจนกว่าจะรีสตาร์ทระบบ)"
                ),
                ip_address=get_client_ip(request),
            )
            messages.success(
                request,
                "บันทึกการตั้งค่าฐานข้อมูลหลักเรียบร้อยแล้ว — จะมีผลหลังรีสตาร์ทระบบเท่านั้น "
                "กรุณารัน migrate บนฐานข้อมูลปลายทางและย้ายข้อมูลเดิมให้ครบก่อนรีสตาร์ทจริง",
            )
        else:
            messages.error(request, "ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง")
    redirect_name = "datasources:browse_index" if user_has(request.user, "datasource.view") else "datasources:connection_list"
    return redirect(reverse(redirect_name) + "?tab=settings")


@login_required
@require_permission("settings.edit")
def primary_database_test(request):
    """AJAX endpoint: tests the SQL Server values currently typed into
    the primary-database form, before anyone saves/restarts anything."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed"}, status=405)
    port_raw = request.POST.get("port", "").strip()
    ok, message = db_utils.test_connection(
        server=request.POST.get("host", "").strip(),
        database=request.POST.get("name", "").strip(),
        username=request.POST.get("user", "").strip(),
        password=request.POST.get("password", ""),
        driver=request.POST.get("odbc_driver", "").strip() or "ODBC Driver 18 for SQL Server",
        port=int(port_raw) if port_raw.isdigit() else None,
    )
    return JsonResponse({"ok": ok, "message": message})
