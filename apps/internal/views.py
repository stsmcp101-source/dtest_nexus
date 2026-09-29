from django.contrib import messages
from apps.audit.services import log_action
from apps.audit.utils import get_client_ip
from django.shortcuts import redirect
from .models import InternalIcon
from .forms import InternalIconSettingsForm
from .icons import INTERNAL_ICONS
from .icon_memory import internal_icon_urls, remember_icon
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.permissions.decorators import require_permission


@login_required
@require_permission("internal.view")
def index(request):
    context = {
        "module_title": "Internal",
        "internal_icon_urls": internal_icon_urls(),
        "module_tag": "INTERNAL",
        "module_description": "For DT section only",
    }
    return render(request, "internal/index.html", context)


@login_required
@require_permission("internal.view")
@require_permission("settings.edit")
def icon_settings(request):
    if request.method == "POST":
        form = InternalIconSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            existing = {icon.key: icon for icon in InternalIcon.objects.all()}
            changed = []
            for key, _section, name, _svg in INTERNAL_ICONS:
                upload = form.cleaned_data[f"icon_{key}"]
                icon = existing.get(key)
                if upload:
                    if not icon:
                        icon = InternalIcon(key=key)
                    icon.image = upload
                    icon.save()
                    changed.append(f"{name}: โลโก้ใหม่")
                elif form.cleaned_data[f"reset_{key}"]:
                    if icon:
                        icon.delete()
                    else:
                        remember_icon(key, None)
                    changed.append(f"{name}: กลับเป็นไอคอนเดิม")
            if changed:
                log_action(
                    user=request.user, action="UPDATE", module="internal", object_type="InternalIcon",
                    description="อัปเดตโลโก้หน้า Internal — " + ", ".join(changed),
                    ip_address=get_client_ip(request),
                )
                messages.success(request, "บันทึกโลโก้เรียบร้อยแล้ว")
            else:
                messages.info(request, "ไม่มีการเปลี่ยนแปลงโลโก้")
            return redirect("internal:index")
    else:
        form = InternalIconSettingsForm()

    icon_urls = internal_icon_urls()
    sections = {}
    for key, section, name, _svg in INTERNAL_ICONS:
        sections.setdefault(section, []).append({
            "key": key, "name": name, "has_custom": key in icon_urls,
            "upload": form[f"icon_{key}"], "reset": form[f"reset_{key}"],
        })
    return render(request, "internal/icon_settings.html", {
        "form": form, "sections": sections, "internal_icon_urls": icon_urls,
    })


