"""
Backend permission enforcement.

Rule #12 (ACCESS CONTROL) is non-negotiable: hiding a menu item is not
security. Every view that touches a protected action must be wrapped
with `require_permission`, which checks the *server-side* session user
against the permission registry and raises PermissionDenied (→ HTTP 403
via apps.core.views.error_403) if the check fails — regardless of what
the frontend does or does not render.
"""
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required as django_login_required

from .registry import user_has

login_required = django_login_required  # re-exported for a single import path


def require_permission(dotted_code):
    """
    View decorator: 403s any request from a user lacking `dotted_code`.

    Usage:
        @login_required
        @require_permission("document.delete")
        def delete_document(request, pk):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not user_has(request.user, dotted_code):
                raise PermissionDenied(
                    f"You do not have the '{dotted_code}' permission required for this action."
                )
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def require_any_permission(*dotted_codes):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not any(user_has(request.user, code) for code in dotted_codes):
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
