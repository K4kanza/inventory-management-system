"""Report building services (US4, role: manager+)."""

from decimal import Decimal

from django.db.models import F

from apps.movements.models import StockMovement
from apps.warehouses.models import StockLevel


def build_valuation(location=None, category=None):
    queryset = (
        StockLevel.objects.filter(product__is_active=True)
        .select_related("product", "location")
        .annotate(unit_cost=F("product__unit_cost"), value=F("quantity") * F("product__unit_cost"))
        .order_by("product__sku", "location__code")
    )
    if location:
        queryset = queryset.filter(location_id=location)
    if category:
        queryset = queryset.filter(product__category_id=category)
    rows = []
    for level in queryset:
        rows.append(
            {
                "sku": level.product.sku,
                "name": level.product.name,
                "location": level.location,
                "quantity": level.quantity,
                "unit_cost": level.unit_cost,
                "value": level.value,
            }
        )
    total = sum((row["value"] for row in rows), Decimal("0.00"))
    return {"rows": rows, "total": total}


def movement_report(item=None, location=None, flow=None, date_from=None):
    queryset = StockMovement.objects.select_related("product", "location", "recorded_by")
    if item:
        queryset = queryset.filter(product__sku=item)
    if location:
        queryset = queryset.filter(location_id=location)
    if flow:
        queryset = queryset.filter(flow=flow)
    if date_from:
        queryset = queryset.filter(recorded_at__date__gte=date_from)
    return queryset
