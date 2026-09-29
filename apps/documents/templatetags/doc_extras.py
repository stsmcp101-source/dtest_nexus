import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def dict_get(mapping, key):
    """Django templates can't index a dict by a variable key (only by a
    literal attribute name), so this fills the gap for lookups like
    documents_by_code|dict_get:spec.report_dev_code."""
    if not mapping:
        return None
    return mapping.get(key)


@register.filter
def highlight(value, term):
    """Wraps every case-insensitive occurrence of `term` in <mark> for the
    live spec-list search. Escapes first so this is safe regardless of
    what's in `value` or `term`, then returns pre-escaped safe HTML."""
    if value is None:
        return ""
    text = escape(str(value))
    term = str(term or "").strip()
    if not term:
        return mark_safe(text)
    pattern = re.compile(re.escape(escape(term)), re.IGNORECASE)
    return mark_safe(pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text))
