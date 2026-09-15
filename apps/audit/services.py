"""
Single entry point for writing audit trail entries.

Every module that performs a security- or business-relevant action
(login, CRUD, upload/download, role/permission changes) should call
`log_action` rather than writing to the AuditLog model directly, so the
write path, error handling, and logger integration stay in one place.
"""
import logging

logger = logging.getLogger("dtest_nexus.audit")


def log_action(*, user, action, module, description="", object_type="", object_id="", ip_address=None):
    # Imported lazily to avoid a circular import between accounts.signals
    # (which fires before the app registry is fully ready) and this
    # module's model import.
    from .models import AuditLog

    is_authenticated = bool(user is not None and getattr(user, "is_authenticated", False))
    try:
        entry = AuditLog.objects.create(
            user=user if is_authenticated else None,
            username_snapshot=user.get_username() if is_authenticated else "anonymous",
            action=action,
            module=module,
            object_type=object_type,
            object_id=str(object_id) if object_id else "",
            description=description,
            ip_address=ip_address,
        )
        logger.info(
            "AUDIT user=%s action=%s module=%s object=%s:%s ip=%s",
            entry.username_snapshot, action, module, object_type, object_id, ip_address,
        )
        return entry
    except Exception:  # noqa: BLE001 - audit logging must never break the request
        logger.exception("Failed to write audit log entry (action=%s, module=%s)", action, module)
        return None
