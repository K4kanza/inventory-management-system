"""Production settings: hardened defaults, PostgreSQL required."""

import os

import dj_database_url

from .base import *  # noqa: F403
from .env import csrf_origins, env_list

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set before starting the production app. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS must list the production domains, comma separated (e.g. example.com,.example.com)"
    )

CSRF_TRUSTED_ORIGINS = csrf_origins()

# Rebind rather than mutate the dict inherited from base: assigning into the
# inherited object would leak into any other settings module loaded in the same
# process.
DATABASES = {
    "default": dj_database_url.config(
        default="",
        conn_max_age=600,
    )
}
if DATABASES["default"].get("ENGINE") != "django.db.backends.postgresql":
    raise RuntimeError("config.settings.production requires a PostgreSQL DATABASE_URL; none was set.")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
