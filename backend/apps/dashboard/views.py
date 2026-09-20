"""Dashboard pages."""

from django.shortcuts import render

from apps.accounts.permissions import Capability, require_capability
from apps.dashboard.services import build_alert_summary


@require_capability(Capability.RECORD_MOVEMENTS)
def dashboard(request):
    summary = build_alert_summary()
    return render(request, "dashboard/dashboard.html", {"summary": summary})
