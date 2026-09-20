"""API routing (see contracts/openapi.yaml)."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.api import views

router = DefaultRouter()
router.register("items", views.ItemViewSet, basename="item")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("locations", views.LocationViewSet, basename="location")
router.register("stock-levels", views.StockLevelViewSet, basename="stock-level")
router.register("movements", views.MovementViewSet, basename="movement")
router.register("users", views.UserViewSet, basename="user")

urlpatterns = router.urls + [
    path("auth/login/", views.ApiLogin.as_view(), name="api-login"),
    path("auth/logout/", views.ApiLogout.as_view(), name="api-logout"),
    path("auth/me/", views.ApiMe.as_view(), name="api-me"),
    path("movements/<int:movement_id>/consent/", views.MovementConsent.as_view(), name="api-consent"),
    path("dashboard/alerts/", views.AlertList.as_view(), name="api-alerts"),
    path("reports/valuation/", views.ValuationReport.as_view(), name="api-valuation"),
    path("reports/movements/", views.MovementsReport.as_view(), name="api-reports-movements"),
    path("reports/low-stock/", views.LowStockReport.as_view(), name="api-low-stock"),
]
