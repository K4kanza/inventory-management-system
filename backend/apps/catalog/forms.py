"""Catalogue and warehouse reference forms."""

from decimal import Decimal

from django import forms
from django.db.models import Q

from apps.catalog.models import Category, Product
from apps.warehouses.models import Location


class ProductForm(forms.ModelForm):
    reorder_level = forms.DecimalField(min_value=Decimal("0"), max_digits=12, decimal_places=3)
    unit_cost = forms.DecimalField(min_value=Decimal("0"), max_digits=12, decimal_places=2)

    class Meta:
        model = Product
        fields = ["sku", "name", "category", "unit", "reorder_level", "unit_cost"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.instance.category.is_active:
            base = Category.objects.filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        else:
            base = Category.objects.filter(is_active=True)
        self.fields["category"].queryset = base
        if self.instance and self.instance.pk:
            self.fields["sku"].disabled = True


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "is_active"]


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["code", "name", "is_active"]
