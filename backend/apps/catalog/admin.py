"""Admin registration for the catalogue."""

from django.contrib import admin

from apps.catalog.models import Category, Product, UnitOfMeasure


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "allow_fractional")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "unit", "reorder_level", "unit_cost", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("sku", "name")
