"""Shared test fixtures."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, UnitOfMeasure
from apps.warehouses.models import Location

User = get_user_model()


def make_user(role, username):
    return User.objects.create_user(username=username, password="password123", role=role)


@pytest.fixture
def staff_user(db):
    return make_user(User.Role.STAFF, "staff")


@pytest.fixture
def manager_user(db):
    return make_user(User.Role.MANAGER, "manager")


@pytest.fixture
def admin_user(db):
    return make_user(User.Role.ADMIN, "admin")


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test category")


@pytest.fixture
def unit(db):
    return UnitOfMeasure.objects.create(name="Piece", symbol="pc")


@pytest.fixture
def fractional_unit(db):
    return UnitOfMeasure.objects.create(name="Kilogram", symbol="kg", allow_fractional=True)


@pytest.fixture
def location(db):
    return Location.objects.create(name="Main warehouse", code="MAIN")


@pytest.fixture
def product(db, category, unit):
    return Product.objects.create(
        sku="SKU-1",
        name="Widget",
        category=category,
        unit=unit,
        reorder_level=Decimal("5"),
        unit_cost=Decimal("2.50"),
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture(autouse=True)
def _skip_postgres_tests_on_other_backends(request):
    if request.node.get_closest_marker("postgres") and connection.vendor != "postgresql":
        pytest.skip("requires a PostgreSQL backend")


@pytest.fixture
def staff_client(staff_user):
    return _client(staff_user)


@pytest.fixture
def manager_client(manager_user):
    return _client(manager_user)


@pytest.fixture
def admin_client(admin_user):
    return _client(admin_user)
