"""Static asset delivery.

Two distinct paths are exercised deliberately:

* ``DEBUG=True`` (local runserver) -- WhiteNoise delegates to the staticfiles
  finders, so ``collectstatic`` is not required for development.
* ``DEBUG=False`` (Vercel) -- assets must come from ``STATIC_ROOT``, which the
  build command populates via ``manage.py collectstatic``.

pytest always runs with DEBUG=False, so each case is selected explicitly.
"""

from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, override_settings

ASSETS = ["admin/css/base.css", "admin/js/core.js"]


def _body(response):
    """WhiteNoise returns a streaming response; normalise it to bytes."""
    if hasattr(response, "streaming_content"):
        return b"".join(response.streaming_content)
    return response.content


def test_whitenoise_middleware_installed():
    assert "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE


def test_static_storage_backend_is_whitenoise():
    backend = settings.STORAGES["staticfiles"]["BACKEND"]
    assert backend == "whitenoise.storage.CompressedStaticFilesStorage"


def test_build_and_runtime_static_storage_agree(monkeypatch):
    """The build runs collectstatic with config.settings.development.

    It does not need DJANGO_SECRET_KEY or DATABASE_URL to collect files, so
    pinning it keeps the build independent of secrets. That is only safe while
    the staticfiles backend lives in base.py and is therefore identical in both
    environments -- if someone moved it into a deployment-only settings module,
    the build would quietly emit uncompressed assets.
    """
    import importlib
    import sys

    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 64)
    monkeypatch.setenv("ALLOWED_HOSTS", "example.test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@placeholder.invalid/neondb")
    monkeypatch.delenv("VERCEL_URL", raising=False)

    sys.modules.pop("config.settings.vercel", None)
    vercel_settings = importlib.import_module("config.settings.vercel")

    assert vercel_settings.STORAGES["staticfiles"] == settings.STORAGES["staticfiles"]
    assert vercel_settings.STATIC_ROOT == settings.STATIC_ROOT
    assert vercel_settings.STATICFILES_DIRS == settings.STATICFILES_DIRS


@pytest.mark.parametrize("asset", ASSETS)
@override_settings(DEBUG=True)
def test_static_asset_served_via_finders_in_development(asset):
    """Development must work on a fresh clone, with no collectstatic run."""
    response = Client().get(f"/static/{asset}")
    assert response.status_code == 200, f"{asset} -> {response.status_code}"
    assert len(_body(response)) > 0


@pytest.mark.parametrize("asset", ASSETS)
def test_static_asset_served_from_static_root_in_production(asset):
    """The Vercel path: DEBUG=False, assets resolved out of STATIC_ROOT."""
    if not (Path(settings.STATIC_ROOT) / asset).exists():
        pytest.skip("run `manage.py collectstatic` to exercise the production path")

    response = Client().get(f"/static/{asset}")
    assert response.status_code == 200, f"{asset} -> {response.status_code}"
    assert len(_body(response)) > 0


def test_admin_login_page_references_its_stylesheet():
    """Regression guard: admin HTML resolves CSS through {% static %}.

    Under a hashed-manifest storage this would raise instead of rendering
    whenever collectstatic had not run.
    """
    response = Client().get("/django-admin/login/")
    assert response.status_code == 200
    assert b"/static/admin/css/base.css" in _body(response)


@pytest.mark.parametrize("asset", ASSETS)
def test_finders_can_resolve_assets(asset):
    assert finders.find(asset) is not None
