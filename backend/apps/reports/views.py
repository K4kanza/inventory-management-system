"""Report pages (US4, role: manager+)."""

from django.shortcuts import render

from apps.accounts.permissions import Capability, require_capability
from apps.dashboard.services import build_alert_summary
from apps.reports.services import build_valuation, movement_report


@require_capability(Capability.VIEW_REPORTS)
def valuation(request):
    report = build_valuation(
        location=request.GET.get("location"),
        category=request.GET.get("category"),
    )
    return render(request, "reports/valuation.html", {"report": report})


@require_capability(Capability.VIEW_REPORTS)
def movements(request):
    rows = movement_report(
        item=request.GET.get("item"),
        location=request.GET.get("location"),
        flow=request.GET.get("flow"),
        date_from=request.GET.get("from"),
    )[:1000]
    return render(request, "reports/movements.html", {"movements": rows})


@require_capability(Capability.VIEW_REPORTS)
def low_stock(request):
    summary = build_alert_summary()
    return render(request, "reports/low_stock.html", {"summary": summary})
