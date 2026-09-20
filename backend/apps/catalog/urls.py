from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("items/", views.item_list, name="item_list"),
    path("items/new/", views.item_new, name="item_new"),
    path("items/<str:sku>/", views.item_detail, name="item_detail"),
    path("items/<str:sku>/edit/", views.item_edit, name="item_edit"),
    path("items/<str:sku>/disable/", views.item_disable, name="item_disable"),
    path("categories/", views.category_list, name="category_list"),
    path("locations/", views.location_list, name="location_list"),
]
