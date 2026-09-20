"""Append-only movement ledger plus pending-consent override workflow."""

from django.db import models


class StockMovement(models.Model):
    class Flow(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        ISSUE = "issue", "Issue"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Direction(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending consent"
        APPLIED = "applied", "Applied"
        CANCELLED = "cancelled", "Cancelled"

    flow = models.CharField(max_length=16, choices=Flow.choices)
    direction = models.CharField(max_length=8, choices=Direction.choices)
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="movements")
    location = models.ForeignKey("warehouses.Location", on_delete=models.PROTECT, related_name="movements")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=500)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="movements")
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.APPLIED, db_index=True)
    requires_override = models.BooleanField(default=False)
    override_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    override_at = models.DateTimeField(null=True, blank=True)
    reconciliation_ref = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-recorded_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="movements_quantity_positive"),
        ]
        indexes = [
            models.Index(fields=["product", "location", "recorded_at"]),
            models.Index(fields=["flow", "recorded_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = StockMovement.objects.get(pk=self.pk)
            immutable_fields = (
                "flow",
                "direction",
                "product",
                "location",
                "quantity",
                "reason",
                "recorded_by",
                "recorded_at",
                "requires_override",
                "reconciliation_ref",
                "unit_cost",
            )
            for field in immutable_fields:
                old_value = getattr(
                    old, f"{field}_id" if field in ("product", "location", "recorded_by") else field
                )
                new_value = getattr(
                    self, f"{field}_id" if field in ("product", "location", "recorded_by") else field
                )
                if old_value != new_value:
                    raise ValueError(f"Movement field '{field}' is immutable; record an adjustment instead.")
        super().save(*args, **kwargs)

    @property
    def signed_quantity(self) -> models.DecimalField:
        if self.direction == self.Direction.IN:
            return self.quantity
        return -self.quantity

    def __str__(self) -> str:
        return f"{self.flow}#{self.pk} {self.product.sku} {self.signed_quantity}"
