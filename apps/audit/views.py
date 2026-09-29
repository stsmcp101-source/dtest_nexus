from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from apps.core.models import PageViewLog, PageViewStat
from apps.permissions.decorators import require_permission
from apps.permissions.registry import user_has

from .models import AuditLog

# ---------------------------------------------------------------------------
# Audit Log and Usage Stats share one page (templates/audit/index.html, tabbed)
# to save top-nav space. Each tab keeps its own real permission gate
# (audit.view / settings.view) and is simply hidden for a user lacking it —
# apps.core.views.usage_stats renders this same template as the other entry
# point, for users who reach it via that URL instead.
# ---------------------------------------------------------------------------


@login_required
@require_permission("audit.view")
def audit_log_list(request):
    can_view_usage = user_has(request.user, "settings.view")
    can_reset_usage = user_has(request.user, "settings.edit")

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
        "initial_tab": "audit",
        "can_view_audit": True,
        "can_view_usage": can_view_usage,
        "can_reset_usage": can_reset_usage,
        "page_obj": page_obj,
        "actions": AuditLog.Action.choices,
        "q": q,
        "selected_action": action,
        "module": module,
    }
    if can_view_usage:
        stats = PageViewStat.objects.order_by("-count")
        monthly = (
            PageViewLog.objects.annotate(month=TruncMonth("visited_at"))
            .values("month").annotate(count=Count("id")).order_by("-month")
        )
        context.update({
            "stats": stats,
            "monthly": monthly,
            "total_visits": stats.aggregate(total=Sum("count"))["total"] or 0,
        })
    return render(request, "audit/index.html", context)
