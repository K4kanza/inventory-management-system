"""Movement recording and history pages (US2)."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import Capability, has_capability, require_capability
from apps.movements.forms import MovementForm
from apps.movements.models import StockMovement
from apps.movements.services import MovementService, OverIssueDenied


@require_capability(Capability.RECORD_MOVEMENTS)
def movement_list(request):
    queryset = StockMovement.objects.select_related("product", "location", "recorded_by")
    item = request.GET.get("item")
    if item:
        queryset = queryset.filter(product__sku=item)
    flow = request.GET.get("flow")
    if flow:
        queryset = queryset.filter(flow=flow)
    paginator = Paginator(queryset, 25)
    movements = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "movements/movement_list.html",
        {"movements": movements, "item": item, "flow": flow},
    )


@require_capability(Capability.RECORD_MOVEMENTS)
@require_http_methods(["GET", "POST"])
def movement_new(request):
    if request.method == "POST":
        form = MovementForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            direction, quantity = form.resolve_direction()
            try:
                movement = MovementService().record(
                    flow=data["flow"],
                    direction=direction,
                    product=data["product"],
                    location=data["location"],
                    quantity=abs(data["quantity"]),
                    reason=data["reason"],
                    recorded_by=request.user,
                    request_override=data["override"],
                    reconciliation_ref=data.get("reconciliation_ref", ""),
                    unit_cost=data.get("unit_cost"),
                )
            except OverIssueDenied as exc:
                messages.error(
                    request,
                    f"Over-issue blocked: available {exc.available}, shortfall {exc.shortfall}. "
                    f"Tick 'request override' to send for manager consent.",
                )
                return render(request, "movements/movement_form.html", {"form": form})
            if movement.status == StockMovement.Status.PENDING:
                messages.warning(request, "Movement recorded as pending; awaiting manager consent.")
            else:
                messages.success(request, "Movement recorded.")
            return redirect("movements:movement_detail", pk=movement.pk)
    else:
        form = MovementForm()
    return render(request, "movements/movement_form.html", {"form": form})


@require_capability(Capability.RECORD_MOVEMENTS)
@require_http_methods(["GET", "POST"])
def movement_detail(request, pk):
    movement = get_object_or_404(
        StockMovement.objects.select_related("product", "location", "recorded_by", "override_by"),
        pk=pk,
    )
    if request.method == "POST" and has_capability(request.user, Capability.APPROVE_OVER_ISSUE):
        approved = request.POST.get("approved") == "true"
        try:
            movement = MovementService().consent(pk, manager=request.user, approved=approved)
        except Exception as exc:  # noqa: BLE001
            messages.error(request, str(exc))
        else:
            messages.success(request, "Consent recorded." if approved else "Consent denied.")
        return redirect("movements:movement_detail", pk=pk)
    can_approve = movement.status == StockMovement.Status.PENDING and has_capability(
        request.user, Capability.APPROVE_OVER_ISSUE
    )
    return render(
        request,
        "movements/movement_detail.html",
        {"movement": movement, "can_approve": can_approve},
    )
