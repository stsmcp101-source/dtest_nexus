from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("utilities.view")
def index(request):
    context = {
        "module_title": "Utilities",
        "module_tag": "MODULE 06 — UTIL",
        "module_description": "เครื่องมือช่วยงานประจำวัน เช่น แบบฟอร์มกลางและตัวช่วยคำนวณ",
    }
    return render(request, "placeholder/coming_soon.html", context)
