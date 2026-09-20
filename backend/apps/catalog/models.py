"""Catalogue entities: Category, UnitOfMeasure, Product."""

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=10)
    allow_fractional = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.symbol})"


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="products")
    reorder_level = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sku"]
        indexes = [models.Index(fields=["category"])]

    def __str__(self) -> str:
        return f"{self.sku} {self.name}"
