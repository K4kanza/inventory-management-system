from django.urls import path

from apps.movements import views

app_name = "movements"

urlpatterns = [
    path("", views.movement_list, name="movement_list"),
    path("new/", views.movement_new, name="movement_new"),
    path("<int:pk>/", views.movement_detail, name="movement_detail"),
]
