from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.audit.models import AuditLog
from apps.core.models import ModuleDefinition
from apps.permissions.decorators import require_permission


@login_required
@require_permission("dashboard.view")
def index(request):
    """
    Authenticated landing page. All figures come from the database —
    no mock/demo numbers (rule #18: 'ข้อมูลต้องมาจาก Database').
    """
    recent_activity = AuditLog.objects.select_related("user")[:8]
    modules = ModuleDefinition.objects.filter(is_active=True).order_by("order")

    context = {
        "recent_activity": recent_activity,
        "modules": modules,
    }
    return render(request, "dashboard/index.html", context)
