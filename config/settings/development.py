"""
Development settings — SQLite, DEBUG=True.

Run with:
    set DJANGO_SETTINGS_MODULE=config.settings.development   (Windows)
    export DJANGO_SETTINGS_MODULE=config.settings.development (Linux/Mac)
This is also the default in manage.py.
"""
import os
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, DATABASE_ENGINE_MAP

DEBUG = True

ALLOWED_HOSTS = ["*"]

if not SECRET_KEY:  # noqa: F405 - convenience fallback, dev only, never used in prod
    SECRET_KEY = "django-insecure-dev-only-key-change-me-在生产环境中必须替换"  # noqa: F405

DATABASE_ENGINE = os.environ.get("DATABASE_ENGINE", "sqlite")

DATABASES = {
    "default": {
        "ENGINE": DATABASE_ENGINE_MAP.get(DATABASE_ENGINE, "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DATABASE_NAME", str(BASE_DIR / "db.sqlite3")),
    }
}

# Relaxed security for local development over http://
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
