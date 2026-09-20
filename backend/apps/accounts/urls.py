from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:user_id>/role/", views.user_role, name="user_role"),
    path("settings/", views.settings_list, name="settings"),
]
