"""Tests für Registrierung, E-Mail-Verifizierung, Login und Passwort-Reset."""

from backend.app.blueprints.auth.routes import EMAIL_VERIFY_SALT, PASSWORD_RESET_SALT
from backend.app.blueprints.auth.tokens import generate_token
from backend.app.extensions import db
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


def test_repeated_login_attempts_never_bypass_email_verification(client):
    """Regressionstest für den gemeldeten Fehler: mehrfaches Einloggen ohne
    den Bestätigungslink zu verwenden darf niemals zum Login führen."""
    client.post("/auth/register", data=REGISTER_DATA)

    for _ in range(3):
        login(client, "neuer_benutzer")
        with client.session_transaction() as session:
            assert "_user_id" not in session


def test_verify_email_get_shows_confirmation_page_without_verifying(client):
    """Sicherheitslücke: ein GET auf den Bestätigungslink durfte das Konto
    bisher sofort verifizieren - automatische E-Mail-Sicherheitsscanner rufen
    Links per GET ab, bevor der Mensch die Mail überhaupt öffnet. Is ein Bad Pattern.."""
    client.post("/auth/register", data=REGISTER_DATA)
    user = User.query.filter_by(username="neuer_benutzer").first()
    token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)

    resp = client.get(f"/auth/verify-email/{token}")

    assert resp.status_code == 200
    assert User.query.filter_by(username="neuer_benutzer").first().email_verified is False


def test_verify_email_post_activates_account_and_allows_login(client):
    client.post("/auth/register", data=REGISTER_DATA)
    user = User.query.filter_by(username="neuer_benutzer").first()
    token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)

    resp = client.post(f"/auth/verify-email/{token}", follow_redirects=True)
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

    token = generate_token([benutzer_user.email, benutzer_user.password_reset_counter], salt=PASSWORD_RESET_SALT)
    resp = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "neuesPasswort1", "confirm_password": "neuesPasswort1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    login(client, benutzer_user.username, password="neuesPasswort1")
    with client.session_transaction() as session:
        assert "_user_id" in session


def test_only_the_latest_requested_reset_link_is_valid(client, benutzer_user):
    """Fordert man mehrmals einen Reset-Link an, war bisher jeder der versendeten
    Links gültig ('first come, first served'). Nur der zuletzt angeforderte darf
    funktionieren, ältere müssen sofort ungültig werden."""
    client.post("/auth/reset-password", data={"email": benutzer_user.email})
    old_counter = db.session.get(User, benutzer_user.id).password_reset_counter
    old_token = generate_token([benutzer_user.email, old_counter], salt=PASSWORD_RESET_SALT)

    client.post("/auth/reset-password", data={"email": benutzer_user.email})
    new_counter = db.session.get(User, benutzer_user.id).password_reset_counter
    new_token = generate_token([benutzer_user.email, new_counter], salt=PASSWORD_RESET_SALT)

    assert old_counter != new_counter

    old_resp = client.post(
        f"/auth/reset-password/{old_token}",
        data={"password": "altesLink1", "confirm_password": "altesLink1"},
        follow_redirects=True,
    )
    assert "bereits verwendet".encode() in old_resp.data

    new_resp = client.post(
        f"/auth/reset-password/{new_token}",
        data={"password": "neuesLink1", "confirm_password": "neuesLink1"},
        follow_redirects=True,
    )
    assert "wurde geändert".encode() in new_resp.data
    assert db.session.get(User, benutzer_user.id).check_password("neuesLink1")


def test_reset_password_token_cannot_be_reused(client, benutzer_user):
    """Sicherheitslücke: derselbe Reset-Link durfte bisher beliebig oft verwendet werden, siehe password_reset_counter auf User."""
    token = generate_token([benutzer_user.email, benutzer_user.password_reset_counter], salt=PASSWORD_RESET_SALT)

    first = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "erstesNeuesPW1", "confirm_password": "erstesNeuesPW1"},
        follow_redirects=True,
    )
    assert "wurde geändert".encode() in first.data

    second = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "zweitesNeuesPW1", "confirm_password": "zweitesNeuesPW1"},
        follow_redirects=True,
    )
    assert "bereits verwendet".encode() in second.data
    assert User.query.filter_by(username=benutzer_user.username).first().check_password("erstesNeuesPW1")


def test_reset_password_rejects_pre_fix_token_format(client, benutzer_user):
    """Ein Token im alten Format (nur die E-Mail, ohne Zähler) muss abgelehnt werden, nicht mit einem 500er abstürzen."""
    old_format_token = generate_token(benutzer_user.email, salt=PASSWORD_RESET_SALT)

    resp = client.post(
        f"/auth/reset-password/{old_format_token}",
        data={"password": "neuesPasswort1", "confirm_password": "neuesPasswort1"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "ungültig".encode() in resp.data


def test_changing_password_invalidates_outstanding_reset_link(client, benutzer_user):
    """Wechselt der Benutzer sein Passwort über 'Mein Konto', wird ein zuvor angeforderter Reset-Link ungültig."""
    token = generate_token([benutzer_user.email, benutzer_user.password_reset_counter], salt=PASSWORD_RESET_SALT)

    login(client, benutzer_user.username)
    client.post(
        "/auth/account/password",
        data={"current_password": "supersecret1", "new_password": "andereskennwort1", "confirm_new_password": "andereskennwort1"},
    )
    client.get("/auth/logout")

    resp = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "gehacktespasswort1", "confirm_password": "gehacktespasswort1"},
        follow_redirects=True,
    )

    assert "bereits verwendet".encode() in resp.data
    assert User.query.filter_by(username=benutzer_user.username).first().check_password("andereskennwort1")
