"""Development settings: relaxed security, local DB (SQLite fallback)."""

import os

from .base import *  # noqa: F403
from .base import BASE_DIR  # noqa: F401

DEBUG = True

# Local work should not require any setup: honour a real secret when one is
# exported, otherwise fall back to a throwaway dev-only key.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY") or "dev-only-insecure-key"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# Let WhiteNoise fall through to the staticfiles finders so a fresh clone works
# without running collectstatic first.
WHITENOISE_USE_FINDERS = True
