"""Read-only admin for the append-only movement ledger (FR-007)."""

from django.contrib import admin

from apps.movements.models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flow",
        "product",
        "location",
        "direction",
        "quantity",
        "recorded_by",
        "recorded_at",
        "status",
    )
    list_filter = ("flow", "status", "recorded_at")
    search_fields = ("product__sku", "reason")
    readonly_fields = (
        "flow",
        "direction",
        "product",
        "location",
        "quantity",
        "reason",
        "recorded_by",
        "recorded_at",
        "status",
        "requires_override",
        "override_by",
        "override_at",
        "reconciliation_ref",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
