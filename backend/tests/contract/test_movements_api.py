"""Contract tests for movements endpoints (FR-004..FR-007, FR-015)."""

import pytest

from apps.movements.models import StockMovement
from apps.warehouses.models import StockLevel


@pytest.mark.django_db
def test_receipt_updates_level(staff_client, product, location):
    response = staff_client.post(
        "/api/movements/",
        {
            "flow": "receipt",
            "product": product.sku,
            "location": location.pk,
            "quantity": "10",
            "reason": "PO-1001",
        },
        format="json",
    )
    assert response.status_code == 201
    level = StockLevel.objects.get(product=product, location=location)
    assert level.quantity == 10
    assert level.status() == "ok"


@pytest.mark.django_db
def test_issue_over_available_without_override_conflict(staff_client, product, location):
    staff_client.post(
        "/api/movements/",
        {"flow": "receipt", "product": product.sku, "location": location.pk, "quantity": "5", "reason": "in"},
        format="json",
    )
    response = staff_client.post(
        "/api/movements/",
        {"flow": "issue", "product": product.sku, "location": location.pk, "quantity": "10", "reason": "out"},
        format="json",
    )
    assert response.status_code == 409
    assert StockMovement.objects.count() == 1


@pytest.mark.django_db
def test_over_issue_with_consent_workflow(staff_client, manager_client, manager_user, product, location):
    staff_client.post(
        "/api/movements/",
        {"flow": "receipt", "product": product.sku, "location": location.pk, "quantity": "5", "reason": "in"},
        format="json",
    )
    pending = staff_client.post(
        "/api/movements/",
        {
            "flow": "issue",
            "product": product.sku,
            "location": location.pk,
            "quantity": "10",
            "reason": "beyond",
            "override": True,
        },
        format="json",
    )
    assert pending.status_code == 201
    movement_id = pending.data["id"]
    assert pending.data["status"] == "pending"
    level = StockLevel.objects.get(product=product, location=location)
    assert level.quantity == 5

    denied = manager_client.post(f"/api/movements/{movement_id}/consent/", {"approved": False}, format="json")
    assert denied.status_code == 200
    assert StockMovement.objects.get(pk=movement_id).status == "cancelled"
    assert StockLevel.objects.get(product=product, location=location).quantity == 5

    pending_2 = staff_client.post(
        "/api/movements/",
        {
            "flow": "issue",
            "product": product.sku,
            "location": location.pk,
            "quantity": "10",
            "reason": "beyond again",
            "override": True,
        },
        format="json",
    )
    approved = manager_client.post(
        f"/api/movements/{pending_2.data['id']}/consent/", {"approved": True}, format="json"
    )
    assert approved.status_code == 200
    movement = StockMovement.objects.get(pk=pending_2.data["id"])
    assert movement.status == "applied"
    assert movement.override_by_id == manager_user.pk
    assert StockLevel.objects.get(product=product, location=location).quantity == -5


@pytest.mark.django_db
def test_staff_cannot_consent(staff_client, product, location, manager_client):
    staff_client.post(
        "/api/movements/",
        {"flow": "receipt", "product": product.sku, "location": location.pk, "quantity": "2", "reason": "in"},
        format="json",
    )
    pending = staff_client.post(
        "/api/movements/",
        {
            "flow": "issue",
            "product": product.sku,
            "location": location.pk,
            "quantity": "5",
            "reason": "over",
            "override": True,
        },
        format="json",
    )
    response = staff_client.post(
        f"/api/movements/{pending.data['id']}/consent/", {"approved": True}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_fractional_quantity_requires_fractional_unit(staff_client, product, location):
    response = staff_client.post(
        "/api/movements/",
        {
            "flow": "receipt",
            "product": product.sku,
            "location": location.pk,
            "quantity": "0.5",
            "reason": "partial",
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_unknown_sku_rejected(staff_client, location):
    response = staff_client.post(
        "/api/movements/",
        {"flow": "receipt", "product": "NOPE", "location": location.pk, "quantity": "1", "reason": "x"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_movement_history_filters(staff_client, product, location):
    staff_client.post(
        "/api/movements/",
        {"flow": "receipt", "product": product.sku, "location": location.pk, "quantity": "3", "reason": "in"},
        format="json",
    )
    staff_client.post(
        "/api/movements/",
        {"flow": "issue", "product": product.sku, "location": location.pk, "quantity": "1", "reason": "out"},
        format="json",
    )
    response = staff_client.get("/api/movements/?flow=receipt")
    assert response.data["count"] == 1
    assert response.data["results"][0]["flow"] == "receipt"
