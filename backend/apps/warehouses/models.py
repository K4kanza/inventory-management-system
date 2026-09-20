"""Warehouse entities: Location and the concurrency-critical StockLevel row."""

from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class StockLevel(models.Model):
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_levels")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="stock_levels")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "location"], name="stock_levels_product_location_key"),
        ]
        indexes = [models.Index(fields=["location"])]

    def status(self) -> str:
        if self.quantity == 0:
            return "out_of_stock"
        if self.quantity <= self.product.reorder_level:
            return "low_stock"
        return "ok"

    def __str__(self) -> str:
        return f"{self.product.sku}@{self.location.code}: {self.quantity}"
