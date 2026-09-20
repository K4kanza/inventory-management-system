"""Smoke tests for the server-rendered pages (templates + access control)."""

import pytest
from django.test import Client


def _logged_in(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_login_page_renders():
    response = Client().get("/accounts/login/")
    assert response.status_code == 200
    assert b"username" in response.content.lower()


@pytest.mark.django_db
def test_dashboard_renders_for_staff(staff_user, product, location):
    response = _logged_in(staff_user).get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_catalog_pages_render(manager_user, product, location):
    client = _logged_in(manager_user)
    for url in [
        "/catalog/items/",
        "/catalog/items/new/",
        f"/catalog/items/{product.sku}/",
        f"/catalog/items/{product.sku}/edit/",
        "/catalog/categories/",
        "/catalog/locations/",
    ]:
        assert client.get(url).status_code == 200, url


@pytest.mark.django_db
def test_movement_pages_render(staff_user, product, location):
    client = _logged_in(staff_user)
    assert client.get("/movements/").status_code == 200
    assert client.get("/movements/new/").status_code == 200


@pytest.mark.django_db
def test_report_pages_render_for_manager(manager_user, product, location):
    client = _logged_in(manager_user)
    assert client.get("/reports/valuation/").status_code == 200
    assert client.get("/reports/movements/").status_code == 200
    assert client.get("/reports/low-stock/").status_code == 200


@pytest.mark.django_db
def test_user_management_requires_admin(staff_user, manager_user, admin_user):
    assert _logged_in(staff_user).get("/users/").status_code in (302, 403)
    assert _logged_in(manager_user).get("/users/").status_code in (302, 403)
    assert _logged_in(admin_user).get("/users/").status_code == 200


@pytest.mark.django_db
def test_settings_require_admin(staff_user, manager_user, admin_user):
    assert _logged_in(staff_user).get("/settings/").status_code in (302, 403)
    assert _logged_in(manager_user).get("/settings/").status_code in (302, 403)
    assert _logged_in(admin_user).get("/settings/").status_code == 200
    response = _logged_in(admin_user).post(
        "/settings/",
        {"key": "low_stock_email", "value": "ops@example.com", "description": "Alert recipient"},
    )
    assert response.status_code == 302
    from apps.accounts.models import GlobalSetting

    assert GlobalSetting.objects.get(key="low_stock_email").value == "ops@example.com"


@pytest.mark.django_db
def test_anonymous_redirected_to_login():
    response = Client().get("/catalog/items/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]
