from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from apps.permissions.decorators import require_permission

from .models import AuditLog


@login_required
@require_permission("audit.view")
def audit_log_list(request):
    logs = AuditLog.objects.select_related("user").all()

    q = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    module = request.GET.get("module", "").strip()

    if q:
        logs = logs.filter(username_snapshot__icontains=q)
    if action:
        logs = logs.filter(action=action)
    if module:
        logs = logs.filter(module__icontains=module)

    paginator = Paginator(logs, getattr(settings, "DEFAULT_PAGE_SIZE", 10))
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "actions": AuditLog.Action.choices,
        "q": q,
        "selected_action": action,
        "module": module,
    }
    return render(request, "audit/audit_log_list.html", context)
