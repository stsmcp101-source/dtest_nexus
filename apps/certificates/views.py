from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("certificates.view")
def index(request):
    context = {
        "module_title": "Certificate",
        "module_tag": "MODULE 03 — CERT",
        "module_description": "ออก ต่ออายุ และติดตามใบรับรองหรือวุฒิบัตรของพนักงานทุกคน",
    }
    return render(request, "placeholder/coming_soon.html", context)
