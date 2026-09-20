from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("valuation/", views.valuation, name="valuation"),
    path("movements/", views.movements, name="movements"),
    path("low-stock/", views.low_stock, name="low_stock"),
]
