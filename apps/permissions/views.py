from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip

from .decorators import require_permission
from .forms import RoleForm
from .models import Role
from .registry import PERMISSION_GROUPS


@login_required
@require_permission("role.view")
def role_list(request):
    roles = Role.objects.select_related("group").all()
    return render(request, "permissions/role_list.html", {"roles": roles})


@login_required
@require_permission("role.create")
def role_create(request):
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            log_action(
                user=request.user, action="ROLE_CHANGE", module="permissions",
                object_type="Role", object_id=role.pk, description=f"Created role '{role.name}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"สร้าง Role '{role.name}' เรียบร้อยแล้ว")
            return redirect("permissions:role_list")
    else:
        form = RoleForm()
    return render(request, "permissions/role_form.html", {"form": form, "mode": "create"})


@login_required
@require_permission("role.edit")
def role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user, action="PERMISSION_CHANGE", module="permissions",
                object_type="Role", object_id=role.pk, description=f"Updated permissions for role '{role.name}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"บันทึกสิทธิ์ของ Role '{role.name}' แล้ว")
            return redirect("permissions:role_list")
    else:
        form = RoleForm(instance=role)
    return render(request, "permissions/role_form.html", {"form": form, "mode": "edit", "role": role})


@login_required
@require_permission("role.delete")
def role_delete(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if role.is_system:
        messages.error(request, "ไม่สามารถลบ System Role นี้ได้")
        return redirect("permissions:role_list")
    if request.method == "POST":
        name = role.name
        role.group.delete()  # cascades to Role via OneToOne
        log_action(
            user=request.user, action="ROLE_CHANGE", module="permissions",
            object_type="Role", object_id=pk, description=f"Deleted role '{name}'.",
            ip_address=get_client_ip(request),
        )
        messages.success(request, f"ลบ Role '{name}' แล้ว")
        return redirect("permissions:role_list")
    return render(request, "permissions/role_confirm_delete.html", {"role": role})


@login_required
@require_permission("role.view")
def permission_matrix(request):
    roles = Role.objects.select_related("group").prefetch_related("group__permissions").all()
    matrix = []
    for group_label, codes in PERMISSION_GROUPS.items():
        rows = []
        for code in codes:
            row = {"code": code, "roles": {}}
            for role in roles:
                from .registry import resolve
                try:
                    app_label, codename = resolve(code).split(".")
                    has = role.group.permissions.filter(content_type__app_label=app_label, codename=codename).exists()
                except Exception:
                    has = False
                row["roles"][role.name] = has
            rows.append(row)
        matrix.append({"group": group_label, "rows": rows})

    return render(request, "permissions/permission_matrix.html", {"roles": roles, "matrix": matrix})
