"""Admin registration for warehouses (read-only stock levels to preserve audit integrity)."""

from django.contrib import admin

from apps.warehouses.models import Location, StockLevel


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity")
    list_filter = ("location",)
    readonly_fields = ("product", "location", "quantity")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
