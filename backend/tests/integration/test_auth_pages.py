"""Smoke tests for django.contrib.auth's registered password URLs.

``config.urls`` mounts ``django.contrib.auth.urls`` wholesale, so all of these
routes are live; before the ``templates/registration/*`` templates existed they
raised TemplateDoesNotExist instead of a 403/404.
"""

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def _logged_in(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_password_change_page_renders(staff_user):
    response = _logged_in(staff_user).get("/accounts/password_change/")
    assert response.status_code == 200
    assert b"old_password" in response.content
    assert b"new_password1" in response.content


@pytest.mark.django_db
def test_password_change_flow_updates_password(staff_user):
    client = _logged_in(staff_user)
    assert (
        client.post(
            "/accounts/password_change/",
            {
                "old_password": "password123",
                "new_password1": "Str0ng-passphrase-991",
                "new_password2": "Str0ng-passphrase-991",
            },
        ).status_code
        == 302
    )

    staff_user.refresh_from_db()
    assert staff_user.check_password("Str0ng-passphrase-991")


@pytest.mark.django_db
def test_password_change_rejects_wrong_current_password(staff_user):
    response = _logged_in(staff_user).post(
        "/accounts/password_change/",
        {
            "old_password": "not-the-password",
            "new_password1": "Str0ng-passphrase-991",
            "new_password2": "Str0ng-passphrase-991",
        },
    )
    assert response.status_code == 200
    assert b"is-invalid" in response.content

    staff_user.refresh_from_db()
    assert staff_user.check_password("password123")


@pytest.mark.django_db
def test_password_reset_page_renders():
    response = Client().get("/accounts/password_reset/")
    assert response.status_code == 200
    assert b"email" in response.content


@pytest.mark.django_db
def test_password_reset_sends_email_and_shows_done_page(admin_user):
    from django.core import mail

    admin_user.email = "admin@example.com"
    admin_user.save(update_fields=["email"])
    mail.outbox.clear()

    response = Client().post("/accounts/password_reset/", {"email": "admin@example.com"})
    assert response.status_code == 302
    assert len(mail.outbox) == 1

    done = Client().get("/accounts/password_reset/done/")
    assert done.status_code == 200
    assert b"Check your email" in done.content


@pytest.mark.django_db
def test_password_reset_confirm_accepts_valid_token(admin_user):
    admin_user.email = "admin@example.com"
    admin_user.set_password("password123")
    admin_user.save(update_fields=["email", "password"])

    uid = urlsafe_base64_encode(force_bytes(admin_user.pk))
    token = default_token_generator.make_token(admin_user)
    url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})

    client = Client()
    # A valid token is exchanged for a session-backed URL so the real token is
    # not left in the browser history.
    redirect = client.get(url)
    assert redirect.status_code == 302

    form_page = client.get(redirect["Location"])
    assert form_page.status_code == 200
    assert b"Set a new password" in form_page.content

    response = client.post(
        redirect["Location"],
        {"new_password1": "Reset-passphrase-4471", "new_password2": "Reset-passphrase-4471"},
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("password_reset_complete")

    admin_user.refresh_from_db()
    assert admin_user.check_password("Reset-passphrase-4471")


@pytest.mark.django_db
def test_password_reset_confirm_rejects_bad_token(admin_user):
    uid = urlsafe_base64_encode(force_bytes(admin_user.pk))
    url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": "not-a-real-token"})

    response = Client().get(url)
    assert response.status_code == 200
    assert b"invalid or has already been used" in response.content


@pytest.mark.django_db
def test_password_reset_complete_page_renders():
    response = Client().get(reverse("password_reset_complete"))
    assert response.status_code == 200
    assert b"Your password has been reset" in response.content


@pytest.mark.django_db
def test_password_change_requires_login():
    response = Client().get("/accounts/password_change/")
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]
