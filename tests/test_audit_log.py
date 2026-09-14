"""Tests für die globale Audit-Log-Ansicht: alle Konfigurationselemente gemeinsam in einer Liste, statt nur pro Objekt."""

from tests.conftest import login


def _field_id(server_type, name: str) -> int:
    return next(f.id for f in server_type.fields if f.name == name)


def test_audit_log_lists_changes_across_all_items(client, admin_user, benutzer_user, server_type):
    """Das globale Audit-Log ist laut RBAC-Matrix Admin-only ("Rechtevergabe/Audit: lesen")."""
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.post(f"/items/new/{server_type.id}", data={"name": "db01", f"field_{ip_field_id}": "10.0.0.20"})
    client.get("/auth/logout")

    login(client, admin_user.username)
    resp = client.get("/admin/audit-log")

    assert resp.status_code == 200
    assert b"web01" in resp.data
    assert b"db01" in resp.data
    assert "Erstellt".encode() in resp.data


def test_betrachter_and_benutzer_cannot_read_audit_log(client, benutzer_user, betrachter_user):
    """Nur Admin darf laut RBAC-Matrix das globale Audit-Log lesen (anders als die Historie pro Objekt)."""
    login(client, benutzer_user.username)
    assert client.get("/admin/audit-log").status_code == 403

    client.get("/auth/logout")
    login(client, betrachter_user.username)
    assert client.get("/admin/audit-log").status_code == 403


def test_anonymous_user_cannot_read_audit_log(client):
    resp = client.get("/admin/audit-log")
    assert resp.status_code == 302
