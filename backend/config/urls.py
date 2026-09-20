"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("movements/", include("apps.movements.urls")),
    path("reports/", include("apps.reports.urls")),
    path("api/", include("apps.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
]
