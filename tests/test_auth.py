"""Tests für Registrierung, E-Mail-Verifizierung, Login und Passwort-Reset."""

from backend.app.blueprints.auth.routes import EMAIL_VERIFY_SALT, PASSWORD_RESET_SALT
from backend.app.blueprints.auth.tokens import generate_token
from backend.app.models import User
from tests.conftest import login

REGISTER_DATA = {
    "username": "neuer_benutzer",
    "first_name": "Neu",
    "last_name": "Benutzer",
    "email": "neu@example.com",
    "password": "supersecret1",
    "confirm_password": "supersecret1",
}


def test_register_creates_unverified_user(client):
    """Selbstregistrierung legt ein Konto an, das erst nach E-Mail-Bestätigung aktiv ist."""
    resp = client.post("/auth/register", data=REGISTER_DATA, follow_redirects=True)

    assert resp.status_code == 200
    user = User.query.filter_by(username="neuer_benutzer").first()
    assert user is not None
    assert user.email_verified is False


def test_login_blocked_before_email_verification(client):
    client.post("/auth/register", data=REGISTER_DATA)

    resp = login(client, "neuer_benutzer")

    with client.session_transaction() as session:
        assert "_user_id" not in session
    assert "bestätige zuerst".encode() in resp.data


def test_verify_email_activates_account_and_allows_login(client):
    client.post("/auth/register", data=REGISTER_DATA)
    user = User.query.filter_by(username="neuer_benutzer").first()
    token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)

    resp = client.get(f"/auth/verify-email/{token}", follow_redirects=True)
    assert resp.status_code == 200
    assert User.query.filter_by(username="neuer_benutzer").first().email_verified is True

    login(client, "neuer_benutzer")
    with client.session_transaction() as session:
        assert "_user_id" in session


def test_verify_email_rejects_invalid_token(client):
    resp = client.get("/auth/verify-email/kaputter-token", follow_redirects=True)
    assert resp.status_code == 200
    assert "ungültig".encode() in resp.data


def test_registration_rejects_duplicate_username(client):
    client.post("/auth/register", data=REGISTER_DATA)

    resp = client.post(
        "/auth/register",
        data={**REGISTER_DATA, "email": "andere@example.com"},
        follow_redirects=True,
    )

    assert "bereits vergeben".encode() in resp.data
    assert User.query.filter_by(username="neuer_benutzer").count() == 1


def test_password_reset_flow(client, benutzer_user):
    reset_resp = client.post("/auth/reset-password", data={"email": benutzer_user.email}, follow_redirects=True)
    assert reset_resp.status_code == 200

    token = generate_token(benutzer_user.email, salt=PASSWORD_RESET_SALT)
    resp = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "neuesPasswort1", "confirm_password": "neuesPasswort1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    login(client, benutzer_user.username, password="neuesPasswort1")
    with client.session_transaction() as session:
        assert "_user_id" in session
