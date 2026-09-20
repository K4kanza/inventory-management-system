"""Development settings: relaxed security, local DB (SQLite fallback)."""

from .base import *  # noqa: F403
from .base import BASE_DIR  # noqa: F401

DEBUG = True

SECRET_KEY = "dev-only-insecure-key"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
