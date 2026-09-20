"""Contract tests for item (catalogue) endpoints."""

import pytest

from apps.catalog.models import Product


@pytest.mark.django_db
def test_list_items(staff_client, product):
    response = staff_client.get("/api/items/")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["sku"] == "SKU-1"


@pytest.mark.django_db
def test_create_item(staff_client, category, unit):
    response = staff_client.post(
        "/api/items/",
        {
            "sku": "SKU-9",
            "name": "Gadget",
            "category": category.pk,
            "unit": unit.pk,
            "reorder_level": "3",
        },
        format="json",
    )
    assert response.status_code == 201
    assert Product.objects.get(sku="SKU-9").name == "Gadget"


@pytest.mark.django_db
def test_duplicate_sku_conflict(staff_client, product):
    response = staff_client.post(
        "/api/items/",
        {
            "sku": "SKU-1",
            "name": "Clone",
            "category": product.category_id,
            "unit": product.unit_id,
            "reorder_level": "1",
        },
        format="json",
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_patch_skipped_when_sku_changes(staff_client, product):
    response = staff_client.patch(f"/api/items/{product.sku}/", {"name": "Updated"}, format="json")
    assert response.status_code == 200
    assert response.data["name"] == "Updated"
    assert response.data["sku"] == "SKU-1"


@pytest.mark.django_db
def test_disable_item(staff_client, product):
    response = staff_client.post(f"/api/items/{product.sku}/disable/")
    assert response.status_code == 200
    product.refresh_from_db()
    assert product.is_active is False


@pytest.mark.django_db
def test_inactive_items_hidden_by_default(staff_client, product):
    product.is_active = False
    product.save()
    response = staff_client.get("/api/items/")
    assert response.data["count"] == 0
    response = staff_client.get("/api/items/?include_disabled=true")
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_search_filter(staff_client, product, category, unit):
    Product.objects.create(sku="SKU-2", name="Sprocket", category=category, unit=unit, reorder_level=0)
    response = staff_client.get("/api/items/?search=sprocket")
    assert response.data["count"] == 1
    assert response.data["results"][0]["sku"] == "SKU-2"


@pytest.mark.django_db
def test_unauthenticated_denied(product):
    from rest_framework.test import APIClient

    response = APIClient().get("/api/items/")
    assert response.status_code in (401, 403)
