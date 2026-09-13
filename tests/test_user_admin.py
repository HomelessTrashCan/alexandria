"""Tests für die Benutzerverwaltung (Rollen zuweisen, Konten deaktivieren)."""

from backend.app.extensions import db
from backend.app.models import User
from domain.roles import Role
from tests.conftest import login


def test_only_admin_can_reach_user_management(client, benutzer_user, admin_user):
    login(client, benutzer_user.username)
    assert client.get("/admin/users").status_code == 403

    client.get("/auth/logout")
    login(client, admin_user.username)
    assert client.get("/admin/users").status_code == 200


def test_admin_can_change_another_users_role(client, admin_user, benutzer_user):
    login(client, admin_user.username)

    resp = client.post(f"/admin/users/{benutzer_user.id}/role", data={"role": Role.BETRACHTER}, follow_redirects=True)

    assert resp.status_code == 200
    assert db.session.get(User, benutzer_user.id).role == Role.BETRACHTER


def test_admin_cannot_change_own_role(client, admin_user):
    """Verhindert eine sofortige Selbstaussperrung."""
    login(client, admin_user.username)

    resp = client.post(f"/admin/users/{admin_user.id}/role", data={"role": Role.BENUTZER}, follow_redirects=True)

    assert resp.status_code == 200
    assert "kann nicht selbst geändert".encode() in resp.data
    assert db.session.get(User, admin_user.id).role == Role.ADMIN


def test_deactivated_user_is_immediately_logged_out(client, admin_user, benutzer_user):
    """Eine laufende Session eines deaktivierten Kontos wird beim nächsten Request beendet, nicht erst bei der nächsten Anmeldung."""
    login(client, benutzer_user.username)
    assert client.get("/items/").status_code == 200
    client.get("/auth/logout")

    login(client, admin_user.username)
    client.post(f"/admin/users/{benutzer_user.id}/toggle-active", follow_redirects=True)
    client.get("/auth/logout")

    # Ein erneuter Login-Versuch muss jetzt verweigert werden.
    resp = client.post("/auth/login", data={"username": benutzer_user.username, "password": "supersecret1"})
    assert "deaktiviert".encode() in resp.data
    assert db.session.get(User, benutzer_user.id).active is False


def test_admin_cannot_deactivate_own_account(client, admin_user):
    login(client, admin_user.username)

    resp = client.post(f"/admin/users/{admin_user.id}/toggle-active", follow_redirects=True)

    assert resp.status_code == 200
    assert "kann nicht selbst deaktiviert".encode() in resp.data
    assert db.session.get(User, admin_user.id).active is True


def test_permissions_matrix_page_is_admin_only(client, benutzer_user, admin_user):
    login(client, benutzer_user.username)
    assert client.get("/admin/permissions").status_code == 403

    client.get("/auth/logout")
    login(client, admin_user.username)
    assert client.get("/admin/permissions").status_code == 200
