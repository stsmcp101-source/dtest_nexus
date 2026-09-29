from django import template

from apps.permissions.registry import user_has

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, dotted_code):
    """
    {% load perms %}
    {% has_perm "document.delete" as can_delete %}
    {% if can_delete %} ... {% endif %}
    """
    request = context.get("request")
    user = getattr(request, "user", None)
    return user_has(user, dotted_code)


@register.filter
def get_item(dictionary, key):
    """Dynamic dict lookup for templates: {{ my_dict|get_item:key_var }}."""
    if not dictionary:
        return None
    return dictionary.get(key)
