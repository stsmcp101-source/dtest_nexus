import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.templatetags.static import static as static_url

from apps.audit.models import AuditLog
from apps.documents.models import Document
from apps.permissions.decorators import require_permission
from apps.permissions.registry import user_has

from .forms import AboutTopicFormSet, HeroBackgroundForm, ModuleImageFormSet, StandardFormSet
from .gif_utils import refresh_module_gif_speed
from .models import AboutTopic, ModuleDefinition, PageViewLog, PageViewStat, Standard, SystemSettings

# Homepage hero background: drop a file named "hero-bg.<ext>" at
# static/img/home/ and it's picked up automatically — no template or
# code edits needed. The image layer always shows (also covers
# animated GIF/WebP, which browsers animate natively via CSS
# background-image); an hero-bg.<video-ext> file, if present, plays on
# top of it. First matching extension in each list wins.
HERO_BG_IMAGE_CANDIDATES = ["jpg", "jpeg", "png", "webp", "gif"]
HERO_BG_VIDEO_CANDIDATES = ["mp4", "webm", "mov", "ogg"]
HERO_BG_VIDEO_MIME_TYPES = {
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "ogg": "video/ogg",
}


def _find_static(path):
    if settings.DEBUG:
        return finders.find(path)
    full_path = os.path.join(settings.STATIC_ROOT or "", path)
    return full_path if os.path.exists(full_path) else None


def _find_hero_bg(candidates):
    for ext in candidates:
        path = f"img/home/hero-bg.{ext}"
        if _find_static(path):
            return path
    return None


def _resolve_hero_bg_image(settings_obj):
    """An admin-uploaded image (see HeroBackgroundForm) always wins over
    the static/img/home/hero-bg.* auto-detect, since an upload gets a
    fresh media URL each time and so can't be served stale from cache
    the way overwriting a static file in place can."""
    if settings_obj.hero_bg_image:
        return settings_obj.hero_bg_image.url
    path = _find_hero_bg(HERO_BG_IMAGE_CANDIDATES)
    return static_url(path) if path else None


def _resolve_hero_bg_video(settings_obj):
    if settings_obj.hero_bg_video:
        ext = settings_obj.hero_bg_video.name.rsplit(".", 1)[-1].lower()
        return settings_obj.hero_bg_video.url, HERO_BG_VIDEO_MIME_TYPES.get(ext)
    path = _find_hero_bg(HERO_BG_VIDEO_CANDIDATES)
    if not path:
        return None, None
    ext = path.rsplit(".", 1)[-1]
    return static_url(path), HERO_BG_VIDEO_MIME_TYPES.get(ext)


def home(request):
    """
    Public landing page, refactored from `dtest-nexus (Home).html`.

    Module cards are real Django-managed data (ModuleDefinition), not
    hard-coded `<a href="#">` markup — each links to a real URL name
    that is resolved in the template with {% url %}.
    """
    modules = ModuleDefinition.objects.filter(is_active=True).order_by("order")
    settings_obj = SystemSettings.get_solo()
    hero_bg_image_url = _resolve_hero_bg_image(settings_obj)
    hero_bg_video_url, hero_bg_video_type = _resolve_hero_bg_video(settings_obj)
    total_visits = PageViewStat.objects.aggregate(total=Sum("count"))["total"] or 0
    return render(request, "core/home.html", {
        "modules": modules,
        "about_topics": AboutTopic.objects.all(),
        "standards": Standard.objects.filter(is_active=True),
        "document_count": Document.objects.count(),
        "hero_bg_image_url": hero_bg_image_url,
        "hero_bg_video_url": hero_bg_video_url,
        "hero_bg_video_type": hero_bg_video_type,
        "total_visits": total_visits,
    })


@login_required
@require_permission("settings.edit")
def home_appearance_settings(request):
    """Combined admin editor for the home page hero background and menu
    strip photos — merged onto one page (was two separate nav links)
    since both just control images shown on the same home page visit.
    Each section is its own <form> (identified by a hidden form_name
    field) so submitting one never disturbs the other's unsaved state."""
    settings_obj = SystemSettings.get_solo()
    module_queryset = ModuleDefinition.objects.order_by("order")

    if request.method == "POST" and request.POST.get("form_name") == "hero":
        hero_form = HeroBackgroundForm(request.POST, request.FILES, instance=settings_obj)
        module_formset = ModuleImageFormSet(queryset=module_queryset)
        if hero_form.is_valid():
            hero_form.save()
            messages.success(request, "อัปเดตพื้นหลังหน้าแรกเรียบร้อยแล้ว")
            return redirect("core:home_appearance_settings")
    elif request.method == "POST" and request.POST.get("form_name") == "modules":
        hero_form = HeroBackgroundForm(instance=settings_obj)
        module_formset = ModuleImageFormSet(request.POST, request.FILES, queryset=module_queryset)
        if module_formset.is_valid():
            saved_modules = module_formset.save()
            for module in saved_modules:
                refresh_module_gif_speed(module)
            messages.success(request, "อัปเดตรูปภาพเมนูเรียบร้อยแล้ว")
            return redirect("core:home_appearance_settings")
    else:
        hero_form = HeroBackgroundForm(instance=settings_obj)
        module_formset = ModuleImageFormSet(queryset=module_queryset)

    return render(request, "core/home_appearance_settings.html", {
        "hero_form": hero_form,
        "module_formset": module_formset,
        "settings_obj": settings_obj,
    })


@login_required
@require_permission("settings.edit")
def about_topics_settings(request):
    """Admin editor for the home page "เกี่ยวกับ" blocks (Policy, Vision,
    Objective, KPI, Contact): text, Thai name and an optional image each."""
    queryset = AboutTopic.objects.order_by("order")
    if request.method == "POST":
        formset = AboutTopicFormSet(request.POST, request.FILES, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "อัปเดตหัวข้อเกี่ยวกับ dTest.nexus เรียบร้อยแล้ว")
            return redirect("core:about_topics_settings")
    else:
        formset = AboutTopicFormSet(queryset=queryset)
    return render(request, "core/about_topics_settings.html", {"formset": formset})


@login_required
@require_permission("settings.edit")
def standards_settings(request):
    """Editor for the home page standards logos, which also fill the
    navbar's Standard > Testing STD. menu: add, remove, re-logo, relink."""
    queryset = Standard.objects.all()
    if request.method == "POST":
        formset = StandardFormSet(request.POST, request.FILES, queryset=queryset, prefix="std")
        if formset.is_valid():
            formset.save()
            messages.success(request, "อัปเดตมาตรฐานเรียบร้อยแล้ว")
            return redirect("core:standards_settings")
    else:
        formset = StandardFormSet(queryset=queryset, prefix="std")
    return render(request, "core/standards_settings.html", {"formset": formset})


@login_required
@require_permission("settings.view")
def usage_stats(request):
    """Admin-only: how many times each page/menu has been visited and
    when it was last visited (see apps.core.middleware.PageViewTrackingMiddleware
    for how these rows get populated), plus a month-by-month rollup.

    Shares one page with Audit Log (templates/audit/index.html, tabbed) to
    save top-nav space — apps.audit.views.audit_log_list is the other entry
    point, for users who reach it via that URL instead. Each tab keeps its
    own real permission gate (settings.view / audit.view / settings.edit)."""
    can_view_audit = user_has(request.user, "audit.view")

    stats = PageViewStat.objects.order_by("-count")
    monthly = (
        PageViewLog.objects.annotate(month=TruncMonth("visited_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("-month")
    )
    context = {
        "initial_tab": "usage",
        "can_view_audit": can_view_audit,
        "can_view_usage": True,
        "can_reset_usage": user_has(request.user, "settings.edit"),
        "stats": stats,
        "monthly": monthly,
        "total_visits": stats.aggregate(total=Sum("count"))["total"] or 0,
    }
    if can_view_audit:
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
        context.update({
            "page_obj": paginator.get_page(request.GET.get("page")),
            "actions": AuditLog.Action.choices,
            "q": q,
            "selected_action": action,
            "module": module,
        })
    return render(request, "audit/index.html", context)


@login_required
@require_permission("settings.edit")
def usage_stats_reset(request):
    """Wipes all visit counters and the monthly detail log — a
    deliberate, confirmed action (see template) since it can't be
    undone."""
    if request.method == "POST":
        PageViewStat.reset_all()
        messages.success(request, "รีเซ็ตยอดเข้าใช้งานทั้งหมดเรียบร้อยแล้ว")
        return redirect("core:usage_stats")
    return render(request, "core/usage_stats_confirm_reset.html")


# ---------------------------------------------------------------------------
# Error handlers (config.urls sets handler400/403/404/500 to these)
# ---------------------------------------------------------------------------
def error_400(request, exception=None):
    return render(request, "errors/400.html", status=400)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
