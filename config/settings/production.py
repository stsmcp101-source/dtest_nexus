"""
Production settings — DEBUG=False, hardened security, SQL Server-ready.

Every value here is read from the environment. Nothing secret is
hard-coded. See .env.example for the full variable list.

To use Microsoft SQL Server / SQL Express in production, install the
optional driver package and set DATABASE_ENGINE=mssql:

    pip install mssql-django

and set:
    DATABASE_ENGINE=mssql
    DATABASE_NAME=dtest_nexus
    DATABASE_HOST=SERVER01
    DATABASE_PORT=1433
    DATABASE_USER=...
    DATABASE_PASSWORD=...
"""
import os
from .base import *  # noqa: F401,F403
from .base import DATABASE_ENGINE_MAP

DEBUG = False

if not SECRET_KEY:  # noqa: F405
    raise RuntimeError(
        "SECRET_KEY environment variable must be set in production. "
        "Refusing to start with an empty secret key."
    )

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS environment variable must be set in production.")

DATABASE_ENGINE = os.environ.get("DATABASE_ENGINE", "mssql")

DATABASES = {
    "default": {
        "ENGINE": DATABASE_ENGINE_MAP.get(DATABASE_ENGINE, "mssql"),
        "NAME": os.environ.get("DATABASE_NAME", "dtest_nexus"),
        "HOST": os.environ.get("DATABASE_HOST", ""),
        "PORT": os.environ.get("DATABASE_PORT", ""),
        "USER": os.environ.get("DATABASE_USER", ""),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
    }
}

if DATABASE_ENGINE == "mssql":
    DATABASES["default"]["OPTIONS"] = {
        "driver": os.environ.get("DATABASE_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
        "extra_params": "TrustServerCertificate=yes;",
    }

# ---------------------------------------------------------------------------
# Hardened security for production
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True") == "True"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "same-origin"
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
