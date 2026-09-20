"""Contract tests for alerts, stock-levels, and reports."""

from decimal import Decimal

import pytest

from apps.catalog.models import Product
from apps.warehouses.models import StockLevel


def seed_stock(product, location, qty):
    StockLevel.objects.create(product=product, location=location, quantity=qty)


@pytest.mark.django_db
def test_alerts_partition(staff_client, product, location, category, unit):
    seed_stock(product, location, Decimal("3"))
    empty = Product.objects.create(
        sku="EMPTY", name="Empty", category=category, unit=unit, reorder_level=Decimal("5")
    )
    seed_stock(empty, location, Decimal("0"))
    response = staff_client.get("/api/dashboard/alerts/")
    assert response.status_code == 200
    assert len(response.data["out_of_stock"]) == 1
    assert response.data["out_of_stock"][0]["sku"] == "EMPTY"
    assert len(response.data["low_stock"]) == 1
    assert response.data["low_stock"][0]["sku"] == "SKU-1"


@pytest.mark.django_db
def test_stock_levels_readout(staff_client, product, location):
    seed_stock(product, location, Decimal("5"))
    response = staff_client.get(f"/api/stock-levels/?location={location.pk}")
    assert response.status_code == 200
    assert response.data[0]["quantity"] == "5.000"


@pytest.mark.django_db
def test_valuation_requires_manager(staff_client, manager_client, product, location):
    seed_stock(product, location, Decimal("10"))
    blocked = staff_client.get("/api/reports/valuation/")
    assert blocked.status_code == 403
    report = manager_client.get("/api/reports/valuation/")
    assert report.status_code == 200
    assert report.data["rows"][0]["value"] == Decimal("25.00")
    assert report.data["total"] == Decimal("25.00")


@pytest.mark.django_db
def test_valuation_totals_across_locations(manager_client, product, location, category, unit):
    seed_stock(product, location, Decimal("10"))
    other = type(location).objects.create(name="Annex", code="ANNEX")
    seed_stock(product, other, Decimal("2"))
    report = manager_client.get("/api/reports/valuation/")
    assert report.data["total"] == Decimal("30.00")


@pytest.mark.django_db
def test_low_stock_report_manager_only(staff_client, manager_client, product, location):
    seed_stock(product, location, Decimal("0"))
    assert staff_client.get("/api/reports/low-stock/").status_code == 403
    response = manager_client.get("/api/reports/low-stock/")
    assert response.status_code == 200
    assert len(response.data["out_of_stock"]) == 1
