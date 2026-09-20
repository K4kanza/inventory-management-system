"""Admin configuration for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import GlobalSetting, User


@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description", "updated_at")
    search_fields = ("key",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
