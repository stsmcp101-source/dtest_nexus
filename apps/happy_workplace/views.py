from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("happy_workplace.view")
def index(request):
    context = {
        "module_title": "Happy Workplace",
        "module_tag": "MODULE 05 — HWP",
        "module_description": "กิจกรรม สวัสดิการ และความเป็นอยู่ที่ดีของพนักงานในองค์กร",
    }
    return render(request, "placeholder/coming_soon.html", context)
