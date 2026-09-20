"""User management pages (US4, role: admin)."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import SettingForm, UserForm
from apps.accounts.models import GlobalSetting
from apps.accounts.permissions import Capability, require_capability

User = get_user_model()


@require_capability(Capability.MANAGE_USERS)
def user_list(request):
    users = User.objects.order_by("username")
    return render(request, "accounts/user_list.html", {"users": users, "roles": User.Role.choices})


@require_capability(Capability.MANAGE_USERS)
@require_http_methods(["GET", "POST"])
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {form.instance.username} created.")
            return redirect("accounts:user_list")
    else:
        form = UserForm()
    return render(request, "accounts/user_form.html", {"form": form, "title": "New user"})


@require_capability(Capability.MANAGE_USERS)
@require_http_methods(["POST"])
def user_role(request, user_id):
    user = User.objects.get(pk=user_id)
    role = request.POST.get("role")
    if role in (User.Role.ADMIN, User.Role.MANAGER, User.Role.STAFF):
        user.role = role
        user.save(update_fields=["role"])
        messages.success(request, f"Role for {user.username} updated to {role}.")
    return redirect("accounts:user_list")


@require_capability(Capability.MANAGE_SETTINGS)
@require_http_methods(["GET", "POST"])
def settings_list(request):
    if request.method == "POST":
        form = SettingForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            setting, created = GlobalSetting.objects.update_or_create(
                key=data["key"],
                defaults={"value": data["value"], "description": data["description"]},
            )
            messages.success(
                request,
                f"Setting '{setting.key}' {'created' if created else 'updated'}.",
            )
            return redirect("accounts:settings")
    else:
        form = SettingForm()
    settings = GlobalSetting.objects.order_by("key")
    return render(
        request,
        "accounts/settings.html",
        {"settings": settings, "form": form},
    )
