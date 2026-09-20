"""Concurrency-safe movement recording (ADR-002).

One StockLevel row per (item, location); writers serialize via SELECT ... FOR
UPDATE. Over-issues require manager consent and go through a pending movement
so the consent is recorded against a concrete ledger id before the balance is
allowed to go negative.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from apps.movements.models import StockMovement
from apps.warehouses.models import StockLevel

ZERO = Decimal("0")
CENT = Decimal("0.01")


class OverIssueDenied(ValidationError):
    def __init__(self, shortfall=None, available=None):
        self.shortfall = shortfall
        self.available = available
        super().__init__(f"Available {available}; requiring {shortfall} more.")


class MovementService:
    def record(
        self,
        *,
        flow,
        direction,
        product,
        location,
        quantity,
        reason,
        recorded_by,
        request_override=False,
        reconciliation_ref="",
        unit_cost=None,
    ):
        self._validate(product, location, quantity, reason, flow, direction)
        try:
            with transaction.atomic():
                return self._record_once(
                    flow=flow,
                    direction=direction,
                    product=product,
                    location=location,
                    quantity=quantity,
                    reason=reason,
                    recorded_by=recorded_by,
                    request_override=request_override,
                    reconciliation_ref=reconciliation_ref,
                    unit_cost=unit_cost,
                )
        except IntegrityError:
            with transaction.atomic():
                return self._record_once(
                    flow=flow,
                    direction=direction,
                    product=product,
                    location=location,
                    quantity=quantity,
                    reason=reason,
                    recorded_by=recorded_by,
                    request_override=request_override,
                    reconciliation_ref=reconciliation_ref,
                    unit_cost=unit_cost,
                )

    def consent(self, movement_id, *, manager, approved):
        if not approved:
            with transaction.atomic():
                movement = self._pending_for_update(movement_id)
                movement.override_by = manager
                movement.override_at = timezone.now()
                movement.status = StockMovement.Status.CANCELLED
                movement.save(update_fields=["override_by", "override_at", "status"])
                return movement
        with transaction.atomic():
            movement = self._pending_for_update(movement_id)
            level = self._get_or_create_locked(movement.product, movement.location)
            level.quantity = level.quantity + movement.signed_quantity
            level.save(update_fields=["quantity"])
            movement.override_by = manager
            movement.override_at = timezone.now()
            movement.status = StockMovement.Status.APPLIED
            movement.save(update_fields=["override_by", "override_at", "status"])
            return movement

    def _pending_for_update(self, movement_id):
        try:
            return (
                StockMovement.objects.select_for_update()
                .select_related("product", "location")
                .get(id=movement_id, status=StockMovement.Status.PENDING)
            )
        except StockMovement.DoesNotExist:
            raise ValidationError("movement is not awaiting consent") from None

    def _record_once(self, **kwargs):
        flow = kwargs["flow"]
        direction = kwargs["direction"]
        product = kwargs["product"]
        location = kwargs["location"]
        quantity = kwargs["quantity"]
        request_override = kwargs["request_override"]
        level = self._get_or_create_locked(product, location)
        new_quantity = level.quantity + self._signed(flow, direction, quantity)
        if new_quantity < ZERO and not request_override:
            raise OverIssueDenied(shortfall=-new_quantity, available=level.quantity)
        if new_quantity < ZERO:
            movement = StockMovement(
                flow=flow,
                direction=direction,
                product=product,
                location=location,
                quantity=quantity,
                reason=kwargs["reason"],
                recorded_by=kwargs["recorded_by"],
                reconciliation_ref=kwargs.get("reconciliation_ref", ""),
                unit_cost=kwargs.get("unit_cost"),
                requires_override=True,
                status=StockMovement.Status.PENDING,
            )
            movement.save()
            return movement
        movement = StockMovement(
            flow=flow,
            direction=direction,
            product=product,
            location=location,
            quantity=quantity,
            reason=kwargs["reason"],
            recorded_by=kwargs["recorded_by"],
            reconciliation_ref=kwargs.get("reconciliation_ref", ""),
            unit_cost=kwargs.get("unit_cost"),
            status=StockMovement.Status.APPLIED,
        )
        movement.save()
        level.quantity = new_quantity
        level.save(update_fields=["quantity"])
        self._revalue(
            product,
            received=quantity if direction == StockMovement.Direction.IN else ZERO,
            receipt_cost=kwargs.get("unit_cost"),
        )
        return movement

    @staticmethod
    def _revalue(product, *, received, receipt_cost):
        """Weighted-average cost: blend the on-hand value with the receipt value."""
        if received <= ZERO or receipt_cost is None:
            return
        total = StockLevel.objects.filter(product=product).aggregate(total=Sum("quantity"))["total"] or ZERO
        if total <= ZERO:
            return
        old_total = total - received
        old_value = old_total * (product.unit_cost or ZERO)
        new_value = old_value + received * receipt_cost
        product.unit_cost = (new_value / total).quantize(CENT, rounding=ROUND_HALF_UP)
        product.save(update_fields=["unit_cost"])

    def _get_or_create_locked(self, product, location):
        try:
            return StockLevel.objects.select_for_update().get(product=product, location=location)
        except StockLevel.DoesNotExist:
            StockLevel.objects.create(product=product, location=location, quantity=ZERO)
            return StockLevel.objects.select_for_update().get(product=product, location=location)

    @staticmethod
    def _signed(flow, direction, quantity):
        if direction == StockMovement.Direction.IN:
            return quantity
        return -quantity

    @staticmethod
    def _validate(product, location, quantity, reason, flow, direction):
        if quantity <= ZERO:
            raise ValidationError("quantity must be a positive magnitude")
        if not product.is_active:
            raise ValidationError("item is disabled")
        if not location.is_active:
            raise ValidationError("location is disabled")
        if not product.unit.allow_fractional and quantity != quantity.to_integral_value():
            raise ValidationError("fractional quantities are not allowed for this unit")
        if not reason or not reason.strip():
            raise ValidationError("reason is required")
        if len(reason) > 500:
            raise ValidationError("reason must be 500 characters or fewer")
        if flow == StockMovement.Flow.ADJUSTMENT and direction not in (
            StockMovement.Direction.IN,
            StockMovement.Direction.OUT,
        ):
            raise ValidationError("adjustment requires a direction")
