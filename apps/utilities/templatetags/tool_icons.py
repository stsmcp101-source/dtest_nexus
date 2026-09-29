from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.utilities.tool_icons import DEFAULT_SVGS

register = template.Library()


@register.simple_tag(takes_context=True)
def tool_logo_url(context, key):
    """Uploaded logo URL for a tile key, or "" — use as {% tool_logo_url "pdf_edit" as logo_url %}."""
    return context.get("tool_icon_urls", {}).get(key, "")


@register.simple_tag(takes_context=True)
def tool_page_icon(context, key):
    """Page header icon for a single-tool page: the uploaded logo, else the tile's default line icon."""
    url = tool_logo_url(context, key)
    if url:
        return format_html('<div class="page-icon has-img"><img src="{}" alt=""></div>', url)
    return format_html(
        '<div class="page-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">{}</svg></div>',
        mark_safe(DEFAULT_SVGS[key]),
    )


@register.simple_tag(takes_context=True)
def tool_icon(context, key):
    """Tile icon box: the admin-uploaded logo if there is one, else the default line icon.
    Expects `tool_icon_urls` ({key: url}) in the template context."""
    url = context.get("tool_icon_urls", {}).get(key)
    if url:
        return format_html('<div class="t-icn has-img"><img src="{}" alt=""></div>', url)
    return format_html(
        '<div class="t-icn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">{}</svg></div>',
        mark_safe(DEFAULT_SVGS[key]),
    )
