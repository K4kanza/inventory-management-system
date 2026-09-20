"""Integration tests for the movement service (ledger integrity, consent, locking, ADR-002)."""

from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.movements.models import StockMovement
from apps.movements.services import MovementService, OverIssueDenied
from apps.warehouses.models import StockLevel

service = MovementService()


@pytest.fixture
def users(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    staff = User.objects.create_user(username="s1", password="x", role=User.Role.STAFF)
    manager = User.objects.create_user(username="m1", password="x", role=User.Role.MANAGER)
    return staff, manager


@pytest.mark.django_db
def test_receipts_and_issues_produce_matching_ledger(users, product, location):
    staff, _ = users
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("10"),
        reason="PO-1",
        recorded_by=staff,
    )
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("5"),
        reason="PO-2",
        recorded_by=staff,
    )
    service.record(
        flow="issue",
        direction="out",
        product=product,
        location=location,
        quantity=Decimal("7"),
        reason="kit",
        recorded_by=staff,
    )
    level = StockLevel.objects.get(product=product, location=location)
    assert level.quantity == Decimal("8.000")
    assert StockMovement.objects.filter(status=StockMovement.Status.APPLIED).count() == 3
    assert level.status() == "ok"


@pytest.mark.django_db
def test_over_issue_without_consent_raises_and_changes_nothing(users, product, location):
    staff, _ = users
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("5"),
        reason="in",
        recorded_by=staff,
    )
    with pytest.raises(OverIssueDenied):
        service.record(
            flow="issue",
            direction="out",
            product=product,
            location=location,
            quantity=Decimal("9"),
            reason="over",
            recorded_by=staff,
        )
    assert StockLevel.objects.get(product=product, location=location).quantity == Decimal("5.000")
    assert StockMovement.objects.count() == 1


@pytest.mark.django_db
def test_consent_approve_applies_negative_balance(users, product, location):
    staff, manager = users
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("5"),
        reason="in",
        recorded_by=staff,
    )
    pending = service.record(
        flow="issue",
        direction="out",
        product=product,
        location=location,
        quantity=Decimal("9"),
        reason="over",
        recorded_by=staff,
        request_override=True,
    )
    assert pending.status == StockMovement.Status.PENDING
    applied = service.consent(pending.pk, manager=manager, approved=True)
    assert applied.status == StockMovement.Status.APPLIED
    assert applied.override_by_id == manager.pk
    assert StockLevel.objects.get(product=product, location=location).quantity == Decimal("-4.000")


@pytest.mark.django_db
def test_consent_deny_cancels_without_changing_level(users, product, location):
    staff, manager = users
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("5"),
        reason="in",
        recorded_by=staff,
    )
    pending = service.record(
        flow="issue",
        direction="out",
        product=product,
        location=location,
        quantity=Decimal("9"),
        reason="over",
        recorded_by=staff,
        request_override=True,
    )
    cancelled = service.consent(pending.pk, manager=manager, approved=False)
    assert cancelled.status == StockMovement.Status.CANCELLED
    assert StockLevel.objects.get(product=product, location=location).quantity == Decimal("5.000")


@pytest.mark.django_db
def test_first_movement_race_retries_once(users, product, location, monkeypatch):
    staff, _ = users
    real_create = StockLevel.objects.create
    calls = {"n": 0}

    def flaky_create(**kwargs):
        if calls["n"] == 0:
            calls["n"] += 1
            raise IntegrityError("unique violation (simulated race)")
        return real_create(**kwargs)

    monkeypatch.setattr(StockLevel.objects, "create", flaky_create)
    movement = service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("3"),
        reason="race",
        recorded_by=staff,
    )
    assert movement.status == StockMovement.Status.APPLIED
    assert calls["n"] == 1
    assert StockLevel.objects.filter(product=product, location=location).count() == 1
    assert StockLevel.objects.get(product=product, location=location).quantity == Decimal("3.000")


@pytest.mark.django_db
def test_ledger_rows_are_immutable(users, product, location):
    staff, _ = users
    movement = service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("3"),
        reason="in",
        recorded_by=staff,
    )
    with pytest.raises(ValueError):
        movement.quantity = Decimal("99")
        movement.save()


@pytest.mark.django_db
def test_fractional_unit_rule(users, product, location, fractional_unit):
    staff, _ = users
    product.unit = fractional_unit
    product.save()
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("0.750"),
        reason="kg in",
        recorded_by=staff,
    )
    level = StockLevel.objects.get(product=product, location=location)
    assert level.quantity == Decimal("0.750")

    from django.core.exceptions import ValidationError

    from apps.catalog.models import UnitOfMeasure

    unit = UnitOfMeasure.objects.create(name="Unit", symbol="u")
    other_product = product.__class__.objects.create(
        sku="INT-1",
        name="Integer",
        category=product.category,
        unit=unit,
        reorder_level=Decimal("0"),
    )
    with pytest.raises(ValidationError):
        service.record(
            flow="receipt",
            direction="in",
            product=other_product,
            location=location,
            quantity=Decimal("0.5"),
            reason="pc in",
            recorded_by=staff,
        )


@pytest.mark.django_db
def test_disabled_product_and_location_blocked(users, product, location):
    staff, _ = users
    from django.core.exceptions import ValidationError

    product.is_active = False
    product.save()
    with pytest.raises(ValidationError):
        service.record(
            flow="receipt",
            direction="in",
            product=product,
            location=location,
            quantity=Decimal("1"),
            reason="x",
            recorded_by=staff,
        )
    product.is_active = True
    product.save()
    location.is_active = False
    location.save()
    with pytest.raises(ValidationError):
        service.record(
            flow="receipt",
            direction="in",
            product=product,
            location=location,
            quantity=Decimal("1"),
            reason="x",
            recorded_by=staff,
        )


@pytest.mark.django_db
def test_receipt_updates_weighted_average_unit_cost(users, product, location):
    staff, _ = users
    product.unit_cost = Decimal("2.00")
    product.save()
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("10"),
        reason="PO-1",
        recorded_by=staff,
        unit_cost=Decimal("3.00"),
    )
    product.refresh_from_db()
    assert product.unit_cost == Decimal("3.00")
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("10"),
        reason="PO-2",
        recorded_by=staff,
        unit_cost=Decimal("1.00"),
    )
    product.refresh_from_db()
    assert product.unit_cost == Decimal("2.00")
    issued = service.record(
        flow="issue",
        direction="out",
        product=product,
        location=location,
        quantity=Decimal("15"),
        reason="out",
        recorded_by=staff,
        unit_cost=Decimal("999.99"),
    )
    product.refresh_from_db()
    assert product.unit_cost == Decimal("2.00")
    assert issued.unit_cost == Decimal("999.99")


@pytest.mark.django_db
def test_adjustment_restores_ledger_and_level_parity(users, product, location):
    staff, _ = users
    service.record(
        flow="receipt",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("10"),
        reason="PO-1",
        recorded_by=staff,
    )
    service.record(
        flow="issue",
        direction="out",
        product=product,
        location=location,
        quantity=Decimal("7"),
        reason="kit",
        recorded_by=staff,
    )
    level = StockLevel.objects.get(product=product, location=location)
    assert level.quantity == Decimal("3.000")
    service.record(
        flow="adjustment",
        direction="in",
        product=product,
        location=location,
        quantity=Decimal("2"),
        reason="recount under-report",
        recorded_by=staff,
        reconciliation_ref="RC-2026-09-16",
    )
    level.refresh_from_db()
    assert level.quantity == Decimal("5.000")
    delta = sum(m.signed_quantity for m in StockMovement.objects.all())
    assert level.quantity == delta


@pytest.mark.postgres
@pytest.mark.django_db(transaction=True)
def test_concurrent_first_movements_serialize(users, product, location):
    """Real race: two writers creating the first StockLevel row concurrently (ADR-002)."""
    import threading

    from apps.catalog.models import Product as P
    from apps.warehouses.models import Location as L

    staff, _ = users
    errors = []
    barrier = threading.Barrier(2)

    def writer():
        try:
            local_product = P.objects.get(pk=product.pk)
            local_location = L.objects.get(pk=location.pk)
            barrier.wait()
            MovementService().record(
                flow="receipt",
                direction="in",
                product=local_product,
                location=local_location,
                quantity=Decimal("1"),
                reason="race",
                recorded_by=staff,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    assert StockLevel.objects.filter(product=product, location=location).count() == 1
    assert StockLevel.objects.get(product=product, location=location).quantity == Decimal("2.000")
