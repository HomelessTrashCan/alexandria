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


NEW_USER_DATA = {
    "username": "neu_vom_admin",
    "first_name": "Neu",
    "last_name": "Vom Admin",
    "email": "neu-vom-admin@example.com",
    "role": Role.BETRACHTER,
    "password": "supersecret1",
    "confirm_password": "supersecret1",
}


def test_admin_can_create_new_user(client, admin_user):
    login(client, admin_user.username)

    resp = client.post("/admin/users/new", data=NEW_USER_DATA, follow_redirects=True)

    assert resp.status_code == 200
    created = User.query.filter_by(username="neu_vom_admin").first()
    assert created is not None
    assert created.role == Role.BETRACHTER
    # Muss wie bei der Selbstregistrierung erst die E-Mailadresse bestätigen.
    assert created.email_verified is False
    assert created.check_password("supersecret1")


def test_create_user_rejects_duplicate_username(client, admin_user, benutzer_user):
    login(client, admin_user.username)

    data = dict(NEW_USER_DATA, username=benutzer_user.username)
    resp = client.post("/admin/users/new", data=data)

    assert resp.status_code == 200
    assert "bereits vergeben".encode() in resp.data


def test_benutzer_cannot_create_user(client, benutzer_user):
    login(client, benutzer_user.username)

    resp = client.post("/admin/users/new", data=NEW_USER_DATA)

    assert resp.status_code == 403
    assert User.query.filter_by(username="neu_vom_admin").first() is None


def test_admin_can_delete_user_without_history(client, admin_user, betrachter_user):
    """Ein Konto ohne verknüpfte Konfigurationselemente/Änderungen lässt sich problemlos löschen."""
    login(client, admin_user.username)

    resp = client.post(f"/admin/users/{betrachter_user.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert "wurde gelöscht".encode() in resp.data
    assert db.session.get(User, betrachter_user.id) is None


def test_admin_cannot_delete_own_account(client, admin_user):
    login(client, admin_user.username)

    resp = client.post(f"/admin/users/{admin_user.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert "kann nicht selbst gelöscht".encode() in resp.data
    assert db.session.get(User, admin_user.id) is not None


def test_delete_user_twice_is_idempotent(client, admin_user, betrachter_user):
    login(client, admin_user.username)
    client.post(f"/admin/users/{betrachter_user.id}/delete")

    resp = client.post(f"/admin/users/{betrachter_user.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert "bereits gelöscht".encode() in resp.data


def test_delete_user_blocked_while_referenced_by_config_item(client, admin_user, benutzer_user, server_type):
    """Ein Konto, das bereits Konfigurationselemente erstellt hat, darf nicht gelöscht werden - das würde die Audit-Historie beschädigen."""
    login(client, benutzer_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.get("/auth/logout")

    login(client, admin_user.username)
    resp = client.post(f"/admin/users/{benutzer_user.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert "kann nicht gelöscht werden".encode() in resp.data
    assert db.session.get(User, benutzer_user.id) is not None
