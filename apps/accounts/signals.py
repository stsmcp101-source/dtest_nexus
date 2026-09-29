from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from apps.audit.services import log_action
from apps.audit.utils import get_client_ip


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    log_action(
        user=user,
        action="LOGIN",
        module="accounts",
        description=f"{user.get_username()} logged in.",
        ip_address=get_client_ip(request) if request else None,
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if user is None:
        return
    log_action(
        user=user,
        action="LOGOUT",
        module="accounts",
        description=f"{user.get_username()} logged out.",
        ip_address=get_client_ip(request) if request else None,
    )


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request=None, **kwargs):
    username = credentials.get("username", "unknown")
    log_action(
        user=None,
        action="LOGIN_FAILED",
        module="accounts",
        description=f"Failed login attempt for username '{username}'.",
        ip_address=get_client_ip(request) if request else None,
    )
