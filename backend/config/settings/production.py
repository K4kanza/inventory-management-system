"""Production settings: hardened defaults, PostgreSQL required."""

import os

import dj_database_url

from .base import *  # noqa: F403
from .base import DATABASES  # noqa: F401

DEBUG = False

ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]

DATABASES["default"] = dj_database_url.config(
    default="postgres://inventory:inventory_dev_password@localhost:5432/inventory",
    conn_max_age=600,
)
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise RuntimeError("production requires a PostgreSQL DATABASE_URL")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]
