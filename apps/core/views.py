from django.shortcuts import render

from apps.documents.models import Document

from .models import ModuleDefinition

# The 7 core work groups the organization is structured around. Kept as
# a single list here (rather than duplicated in the template) so the
# nav dropdown, the "โครงสร้างองค์กร" section, and the homepage stat
# count all stay in sync automatically.
ORG_GROUPS = ["RAC", "PAC", "SOUND", "EMC", "SAMPLING", "SUPPORT", "ISO"]


def home(request):
    """
    Public landing page, refactored from `dtest-nexus (Home).html`.

    Module cards are real Django-managed data (ModuleDefinition), not
    hard-coded `<a href="#">` markup — each links to a real URL name
    that is resolved in the template with {% url %}.
    """
    modules = ModuleDefinition.objects.filter(is_active=True).order_by("order")
    return render(request, "core/home.html", {
        "modules": modules,
        "org_groups": ORG_GROUPS,
        "document_count": Document.objects.count(),
    })


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
