"""Dashboard alert aggregation (FR-008/FR-009)."""

from django.db.models import F

from apps.warehouses.models import StockLevel


def build_alert_summary(location=None):
    queryset = (
        StockLevel.objects.filter(product__is_active=True)
        .annotate(product_sku=F("product__sku"), product_name=F("product__name"))
        .select_related("product", "location", "product__category", "product__unit")
        .filter(quantity__lte=F("product__reorder_level"))
        .order_by("product__sku", "location__code")
    )
    if location:
        queryset = queryset.filter(location_id=location)
    low_stock = []
    out_of_stock = []
    for level in queryset:
        row = {
            "sku": level.product.sku,
            "name": level.product.name,
            "location": level.location,
            "quantity": level.quantity,
            "reorder_level": level.product.reorder_level,
            "status": level.status(),
        }
        if level.status() == "out_of_stock":
            out_of_stock.append(row)
        else:
            low_stock.append(row)
    return {"low_stock": low_stock, "out_of_stock": out_of_stock}
