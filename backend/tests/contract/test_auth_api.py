"""Contract tests for the auth endpoints."""

import pytest


@pytest.mark.django_db
def test_login_returns_user(staff_user, staff_client):
    client = staff_client
    client.logout()
    response = client.post(
        "/api/auth/login/", {"username": "staff", "password": "password123"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["username"] == "staff"
    assert response.data["role"] == "staff"


@pytest.mark.django_db
def test_login_invalid_credentials(staff_client):
    client = staff_client
    client.logout()
    response = client.post("/api/auth/login/", {"username": "staff", "password": "wrong"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user(staff_client):
    response = staff_client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["username"] == "staff"


@pytest.mark.django_db
def test_logout_ends_session(staff_user):
    from rest_framework.test import APIClient

    client = APIClient()
    assert (
        client.post(
            "/api/auth/login/", {"username": "staff", "password": "password123"}, format="json"
        ).status_code
        == 200
    )
    assert client.get("/api/auth/me/").status_code == 200
    assert client.post("/api/auth/logout/").status_code == 204
    assert client.get("/api/auth/me/").status_code == 401
