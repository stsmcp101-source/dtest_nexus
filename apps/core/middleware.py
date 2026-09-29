from .models import ModuleDefinition, PageViewStat


class PageViewTrackingMiddleware:
    """
    Records one hit against PageViewStat for every successful page load
    of the Home page or an active module (Document Data, Employees, ...).
    Reads ModuleDefinition rather than a hard-coded URL list, so a module
    added later is tracked automatically with no code change here.

    Deliberately narrow: only GET requests that resolved to a real view
    and returned 200 count as a "visit" — POSTs, redirects, downloads,
    and API-style JSON endpoints (search-suggest, spec rows, etc.) don't.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._record(request, response)
        return response

    def _record(self, request, response):
        if request.method != "GET" or response.status_code != 200:
            return
        match = getattr(request, "resolver_match", None)
        if not match or not match.view_name:
            return

        view_name = match.view_name
        if view_name == "core:home":
            PageViewStat.record_visit("home", "หน้าแรก (Home)")
            return

        module = ModuleDefinition.objects.filter(url_name=view_name, is_active=True).first()
        if module:
            PageViewStat.record_visit(module.code, module.name)
