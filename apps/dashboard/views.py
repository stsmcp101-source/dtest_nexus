from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.core.models import ModuleDefinition
from apps.permissions.decorators import require_permission

from apps.documents.models import Document


@login_required
@require_permission("dashboard.view")
def index(request):
    """
    Authenticated landing page. All figures come from the database —
    no mock/demo numbers (rule #18: 'ข้อมูลต้องมาจาก Database').
    """
    documents_qs = Document.objects.all()
    total_documents = documents_qs.count()
    dev_documents = documents_qs.filter(category__code="dev").count()
    mass_documents = documents_qs.filter(category__code="mass").count()

    recent_activity = AuditLog.objects.select_related("user")[:8]
    modules = ModuleDefinition.objects.filter(is_active=True).order_by("order")

    context = {
        "total_documents": total_documents,
        "dev_documents": dev_documents,
        "mass_documents": mass_documents,
        "recent_activity": recent_activity,
        "modules": modules,
        "now": timezone.now(),
    }
    return render(request, "dashboard/index.html", context)
