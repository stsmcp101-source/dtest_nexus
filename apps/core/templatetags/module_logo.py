from django import template

from apps.core.models import ModuleDefinition

register = template.Library()


@register.simple_tag(takes_context=True)
def module_logo_url(context):
    """Home-page menu image (set on the "รูปภาพหน้าแรก" page) of the module the
    current page belongs to, matched by URL namespace — or "" if it has none.
    Use as {% module_logo_url as module_logo %} on a module's landing page."""
    match = getattr(context.get("request"), "resolver_match", None)
    if not match or not match.namespace:
        return ""
    module = ModuleDefinition.objects.filter(url_name__startswith=f"{match.namespace}:").first()
    if not module or not module.background_image:
        return ""
    return (module.background_image_processed or module.background_image).url
