"""Contract tests for admin user management (US4, FR-010)."""

import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_admin_creates_user(admin_client):
    response = admin_client.post(
        "/api/users/",
        {"username": "newbie", "password": "a-strong-password", "role": "staff"},
        format="json",
    )
    assert response.status_code == 201
    user = User.objects.get(username="newbie")
    assert user.check_password("a-strong-password")


@pytest.mark.django_db
def test_staff_cannot_list_users(staff_client):
    response = staff_client.get("/api/users/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_manager_cannot_change_roles(manager_client, staff_user):
    response = manager_client.patch(f"/api/users/{staff_user.pk}/role/", {"role": "manager"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_changes_role(admin_client, staff_user):
    response = admin_client.patch(f"/api/users/{staff_user.pk}/role/", {"role": "manager"}, format="json")
    assert response.status_code == 200
    staff_user.refresh_from_db()
    assert staff_user.role == User.Role.MANAGER
