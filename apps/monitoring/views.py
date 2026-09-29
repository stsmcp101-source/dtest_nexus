from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("monitoring.view")
def index(request):
    context = {
        "module_title": "Monitoring & Dashboard",
        "module_tag": "MODULE 04 — MON",
        "module_description": "ภาพรวมข้อมูลและตัวชี้วัดสำคัญขององค์กรแบบเรียลไทม์",
    }
    return render(request, "placeholder/coming_soon.html", context)
