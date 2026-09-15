from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("employees.view")
def index(request):
    context = {
        "module_title": "จัดการพนักงาน",
        "module_tag": "MODULE 02 — HR",
        "module_description": "ข้อมูลพนักงาน การลา และประวัติการทำงานครบถ้วนในระบบเดียว",
    }
    return render(request, "placeholder/coming_soon.html", context)
