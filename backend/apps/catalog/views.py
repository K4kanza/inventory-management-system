"""Catalogue pages (US1)."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import Capability, require_capability
from apps.catalog.forms import CategoryForm, LocationForm, ProductForm
from apps.catalog.models import Category, Product
from apps.warehouses.models import Location


@require_capability(Capability.MANAGE_ITEMS)
def item_list(request):
    queryset = Product.objects.select_related("category", "unit")
    search = request.GET.get("search")
    if search:
        queryset = queryset.filter(
            Q(sku__icontains=search) | Q(name__icontains=search) | Q(category__name__icontains=search)
        )
    include_disabled = request.GET.get("include_disabled") == "true"
    if not include_disabled:
        queryset = queryset.filter(is_active=True)
    paginator = Paginator(queryset, 25)
    items = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "catalog/item_list.html",
        {"items": items, "search": search, "include_disabled": include_disabled},
    )


@require_capability(Capability.MANAGE_ITEMS)
@require_http_methods(["GET", "POST"])
def item_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item {form.instance.sku} created.")
            return redirect("catalog:item_list")
    else:
        form = ProductForm()
    return render(request, "catalog/item_form.html", {"form": form, "title": "New item"})


@require_capability(Capability.MANAGE_ITEMS)
@require_http_methods(["GET", "POST"])
def item_edit(request, sku):
    item = get_object_or_404(Product, sku=sku)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated.")
            return redirect("catalog:item_detail", sku=item.sku)
    else:
        form = ProductForm(instance=item)
    return render(
        request, "catalog/item_form.html", {"form": form, "item": item, "title": f"Edit {item.sku}"}
    )


@require_capability(Capability.MANAGE_ITEMS)
@require_http_methods(["POST"])
def item_disable(request, sku):
    item = get_object_or_404(Product, sku=sku)
    item.is_active = False
    item.save(update_fields=["is_active", "updated_at"])
    messages.success(request, f"{item.sku} disabled.")
    return redirect("catalog:item_detail", sku=item.sku)


@require_capability(Capability.MANAGE_ITEMS)
@require_http_methods(["GET", "POST"])
def item_detail(request, sku):
    item = get_object_or_404(Product.objects.select_related("category", "unit"), sku=sku)
    levels = item.stock_levels.select_related("location").all()
    return render(request, "catalog/item_detail.html", {"item": item, "levels": levels})


@require_capability(Capability.MANAGE_ITEMS)
def category_list(request):
    categories = Category.objects.all()
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect("catalog:category_list")
    return render(
        request, "catalog/reference_list.html", {"categories": categories, "form": form, "kind": "Category"}
    )


@require_capability(Capability.MANAGE_ITEMS)
def location_list(request):
    locations = Location.objects.all()
    form = LocationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Location created.")
        return redirect("catalog:location_list")
    return render(
        request, "catalog/reference_list.html", {"locations": locations, "form": form, "kind": "Location"}
    )
