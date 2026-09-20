"""Movement recording form."""

from django import forms

from apps.catalog.models import Product
from apps.movements.models import StockMovement
from apps.warehouses.models import Location


class MovementForm(forms.Form):
    flow = forms.ChoiceField(choices=StockMovement.Flow.choices)
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).select_related("unit"),
        to_field_name="sku",
        label="Item (SKU)",
    )
    location = forms.ModelChoiceField(queryset=Location.objects.filter(is_active=True))
    quantity = forms.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    reason = forms.CharField(max_length=500)
    direction_modifier = forms.ChoiceField(
        choices=(("in", "In (increase)"), ("out", "Out (decrease)")),
        initial="in",
        required=False,
        label="Adjustment direction",
        help_text="Only used for adjustment movements.",
    )
    override = forms.BooleanField(required=False, label="Request manager override (over-issue)")
    reconciliation_ref = forms.CharField(required=False, max_length=100, label="Reconciliation reference")
    unit_cost = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=0,
        label="Receipt unit cost",
        help_text="Unit cost for weighted-average valuation (receipts only; optional).",
    )

    def resolve_direction(self):
        flow = self.cleaned_data["flow"]
        quantity = self.cleaned_data["quantity"]
        if flow == StockMovement.Flow.RECEIPT:
            return StockMovement.Direction.IN, quantity
        if flow == StockMovement.Flow.ISSUE:
            return StockMovement.Direction.OUT, quantity
        if self.cleaned_data.get("direction_modifier") == "out":
            return StockMovement.Direction.OUT, quantity
        return StockMovement.Direction.IN, quantity
