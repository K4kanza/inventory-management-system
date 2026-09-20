"""Custom user model with a single role per account (FR-010)."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STAFF, db_index=True)

    def has_capability(self, capability: str) -> bool:
        from apps.accounts.permissions import capabilities_for

        return self.is_active and capability in capabilities_for(self.role)

    @property
    def capabilities(self) -> set[str]:
        from apps.accounts.permissions import capabilities_for

        return capabilities_for(self.role) if self.is_active else set()

    def __str__(self) -> str:
        return self.get_username()


class GlobalSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.key}={self.value}"
