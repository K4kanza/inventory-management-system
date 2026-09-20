"""Single source of truth for role capabilities and default-deny permission checks."""

from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class Capability:
    MANAGE_ITEMS = "manage_items"
    RECORD_MOVEMENTS = "record_movements"
    APPROVE_OVER_ISSUE = "approve_over_issue"
    VIEW_REPORTS = "view_reports"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"

    ALL = {
        MANAGE_ITEMS,
        RECORD_MOVEMENTS,
        APPROVE_OVER_ISSUE,
        VIEW_REPORTS,
        MANAGE_USERS,
        MANAGE_SETTINGS,
    }


ROLE_CAPABILITIES: dict[str, set[str]] = {
    User.Role.ADMIN: set(Capability.ALL),
    User.Role.MANAGER: {
        Capability.MANAGE_ITEMS,
        Capability.RECORD_MOVEMENTS,
        Capability.APPROVE_OVER_ISSUE,
        Capability.VIEW_REPORTS,
    },
    User.Role.STAFF: {
        Capability.MANAGE_ITEMS,
        Capability.RECORD_MOVEMENTS,
    },
}


def capabilities_for(role: str) -> set[str]:
    return set(ROLE_CAPABILITIES.get(role, ()))


def has_capability(user, capability: str) -> bool:
    return bool(
        user and user.is_authenticated and user.is_active and capability in capabilities_for(user.role)
    )


def require_capability(capability: str):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            if not has_capability(request.user, capability):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


class RequireRolePermission(BasePermission):
    """DRF default-deny: a view must declare ``required_capability`` and the
    authenticated caller must hold that capability."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        capability = getattr(view, "required_capability", None)
        if capability is None:
            return bool(request.user and request.user.is_authenticated)
        return has_capability(request.user, capability)
