from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_login_out
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from apps.permissions.decorators import require_permission

from .forms import UserForm
from .models import User

UserModel = get_user_model()


class StyledLoginView(LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")
        return super().form_invalid(form)


@login_required
def logout_view(request):
    auth_login_out(request)
    messages.info(request, "ออกจากระบบเรียบร้อยแล้ว")
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
@require_permission("user.view")
def user_list(request):
    users = User.objects.select_related("department").prefetch_related("groups").all()

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    role = request.GET.get("role", "").strip()

    if q:
        users = users.filter(username__icontains=q) | users.filter(
            first_name__icontains=q
        ) | users.filter(last_name__icontains=q) | users.filter(employee_id__icontains=q)
    if status:
        users = users.filter(status=status)
    if role:
        users = users.filter(groups__name=role)

    users = users.distinct().order_by("-date_joined")

    paginator = Paginator(users, getattr(settings, "DEFAULT_PAGE_SIZE", 10))
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "role": role,
        "status_choices": User.Status.choices,
    }
    return render(request, "accounts/user_list.html", context)


@login_required
@require_permission("user.create")
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(
                user=request.user, action="CREATE", module="accounts",
                object_type="User", object_id=user.pk,
                description=f"Created user '{user.username}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"สร้างผู้ใช้งาน '{user.username}' เรียบร้อยแล้ว")
            return redirect("accounts:user_list")
    else:
        form = UserForm()
    return render(request, "accounts/user_form.html", {"form": form, "mode": "create"})


@login_required
@require_permission("user.edit")
def user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user, action="UPDATE", module="accounts",
                object_type="User", object_id=user_obj.pk,
                description=f"Updated user '{user_obj.username}'.",
                ip_address=get_client_ip(request),
            )
            messages.success(request, f"บันทึกข้อมูลผู้ใช้งาน '{user_obj.username}' แล้ว")
            return redirect("accounts:user_list")
    else:
        form = UserForm(instance=user_obj)
    return render(request, "accounts/user_form.html", {"form": form, "mode": "edit", "user_obj": user_obj})


@login_required
@require_permission("user.delete")
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        username = user_obj.username
        user_obj.delete()
        log_action(
            user=request.user, action="DELETE", module="accounts",
            object_type="User", object_id=pk, description=f"Deleted user '{username}'.",
            ip_address=get_client_ip(request),
        )
        messages.success(request, f"ลบผู้ใช้งาน '{username}' แล้ว")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_confirm_delete.html", {"user_obj": user_obj})


@login_required
@require_permission("user.edit")
def user_toggle_status(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if user_obj.status == User.Status.ACTIVE:
            user_obj.status = User.Status.DISABLED
            user_obj.is_active = False
            action_desc = "disabled"
        else:
            user_obj.status = User.Status.ACTIVE
            user_obj.is_active = True
            action_desc = "activated"
        user_obj.save(update_fields=["status", "is_active"])
        log_action(
            user=request.user, action="UPDATE", module="accounts",
            object_type="User", object_id=user_obj.pk,
            description=f"User '{user_obj.username}' {action_desc}.",
            ip_address=get_client_ip(request),
        )
        messages.success(request, f"บัญชี '{user_obj.username}' ถูก{'ปิดใช้งาน' if action_desc=='disabled' else 'เปิดใช้งาน'}แล้ว")
    return redirect("accounts:user_list")


@login_required
@require_permission("user.reset_password")
def user_reset_password(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        temp_password = get_random_string(12)
        user_obj.set_password(temp_password)
        user_obj.must_change_password = True
        user_obj.save(update_fields=["password", "must_change_password"])
        log_action(
            user=request.user, action="PASSWORD_CHANGE", module="accounts",
            object_type="User", object_id=user_obj.pk,
            description=f"Password reset for '{user_obj.username}' by {request.user.get_username()}.",
            ip_address=get_client_ip(request),
        )
        messages.success(
            request,
            f"ตั้งรหัสผ่านชั่วคราวสำหรับ '{user_obj.username}' แล้ว: {temp_password} "
            "(กรุณาแจ้งผู้ใช้งานให้เปลี่ยนรหัสผ่านทันทีที่เข้าสู่ระบบ)",
        )
    return redirect("accounts:user_list")
