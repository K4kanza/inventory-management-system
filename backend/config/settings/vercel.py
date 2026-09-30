"""Vercel serverless settings: read-only FS-safe, PostgreSQL via DATABASE_URL.

Deployment configuration (secret key, host allow-list, CSRF origins) is read
from the Vercel project environment. Anything missing raises at import time so
a misconfigured deploy fails loudly instead of silently booting against an
empty database -- the failure mode that makes valid credentials look broken.
"""

import os

import dj_database_url

from .base import *  # noqa: F403
from .env import csrf_origins, env_list

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set on the Vercel project. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))" '
        "then add it with: vercel env add DJANGO_SECRET_KEY production"
    )

# ALLOWED_HOSTS is the authoritative allow-list for custom domains. VERCEL_URL
# (the active deployment) and the *.vercel.app wildcard are appended so preview
# deployments keep working without editing env vars per preview.
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
ALLOWED_HOSTS.append(os.environ.get("VERCEL_URL", ""))
ALLOWED_HOSTS.append(".vercel.app")
ALLOWED_HOSTS = [host for host in dict.fromkeys(ALLOWED_HOSTS) if host]

# Required for session-authenticated POSTs (login, logout, DRF SessionAuthentication)
# once a custom domain or a separate frontend origin is introduced.
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
    raise RuntimeError(
        "config.settings.vercel requires a PostgreSQL DATABASE_URL. The Neon "
        "integration on the Vercel project supplies it; an in-memory SQLite "
        "fallback would lose every user and session between invocations."
    )

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SECURE_SSL_REDIRECT is deliberately left off: Vercel terminates TLS at the
# edge and always sets X-Forwarded-Proto, so the app never sees plain HTTP and
# the redirect would only risk a loop.

# Vercel terminates TLS and forwards the original scheme in this header;
# without it Django would treat every request as plain HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
