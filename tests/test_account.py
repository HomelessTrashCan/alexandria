"""Tests für das Self-Service-Portal (Mein Konto): eigenes Profil bearbeiten, eigenes Kennwort ändern."""

from backend.app.extensions import db
from backend.app.models import User
from tests.conftest import login


def test_account_page_shows_current_profile(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.get("/auth/account")

    assert resp.status_code == 200
    assert benutzer_user.first_name.encode() in resp.data
    assert benutzer_user.email.encode() in resp.data


def test_benutzer_can_change_own_name(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.post("/auth/account", data={"first_name": "Neuervorname", "last_name": "Neuernachname"}, follow_redirects=True)

    assert resp.status_code == 200
    updated = db.session.get(User, benutzer_user.id)
    assert updated.first_name == "Neuervorname"
    assert updated.last_name == "Neuernachname"


def test_benutzer_cannot_change_own_email(client, benutzer_user):
    """AccountForm (nicht-Admin) kennt gar kein E-Mail-Feld - ein untergeschobenes 'email' im POST wird ignoriert."""
    login(client, benutzer_user.username)
    original_email = benutzer_user.email

    client.post(
        "/auth/account",
        data={"first_name": benutzer_user.first_name, "last_name": benutzer_user.last_name, "email": "gehackt@example.com"},
        follow_redirects=True,
    )

    assert db.session.get(User, benutzer_user.id).email == original_email


def test_admin_can_change_own_email_and_must_reverify(client, admin_user):
    login(client, admin_user.username)

    resp = client.post(
        "/auth/account",
        data={"first_name": admin_user.first_name, "last_name": admin_user.last_name, "email": "neue-admin-adresse@example.com"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    updated = db.session.get(User, admin_user.id)
    assert updated.email == "neue-admin-adresse@example.com"
    # Eine neue, unbestätigte Adresse darf nicht sofort als verifiziert gelten.
    assert updated.email_verified is False

    # Die laufende Session bleibt gültig (kein sofortiger Logout)...
    assert client.get("/items/").status_code == 200

    # ...aber ein neuer Login-Versuch wird verweigert, bis die neue Adresse bestätigt ist.
    client.get("/auth/logout")
    resp = client.post("/auth/login", data={"username": admin_user.username, "password": "supersecret1"})
    assert "bestätige zuerst".encode() in resp.data


def test_change_own_password_success(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.post(
        "/auth/account/password",
        data={"current_password": "supersecret1", "new_password": "einneueskennwort", "confirm_new_password": "einneueskennwort"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "wurde geändert".encode() in resp.data
    assert db.session.get(User, benutzer_user.id).check_password("einneueskennwort")

    client.get("/auth/logout")
    login_resp = client.post("/auth/login", data={"username": benutzer_user.username, "password": "einneueskennwort"}, follow_redirects=True)
    assert login_resp.status_code == 200


def test_change_own_password_rejects_wrong_current_password(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.post(
        "/auth/account/password",
        data={"current_password": "falsches-kennwort", "new_password": "einneueskennwort", "confirm_new_password": "einneueskennwort"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "ist falsch".encode() in resp.data
    assert db.session.get(User, benutzer_user.id).check_password("supersecret1")


def test_change_own_password_rejects_mismatched_confirmation(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.post(
        "/auth/account/password",
        data={"current_password": "supersecret1", "new_password": "einneueskennwort", "confirm_new_password": "einanderswort"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "stimmen nicht überein".encode() in resp.data
    assert db.session.get(User, benutzer_user.id).check_password("supersecret1")


def test_anonymous_user_cannot_reach_account_page(client):
    resp = client.get("/auth/account")
    assert resp.status_code == 302
