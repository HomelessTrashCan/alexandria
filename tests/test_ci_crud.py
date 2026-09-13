"""Tests für CRUD an Konfigurationselementen."""

from backend.app.extensions import db
from backend.app.models import ChangeLogEntry, ConfigItem
from tests.conftest import login


def _field_id(server_type, name: str) -> int:
    return next(f.id for f in server_type.fields if f.name == name)


def test_create_config_item_with_field_values(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")

    resp = client.post(
        f"/items/new/{server_type.id}",
        data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    item = ConfigItem.query.filter_by(name="web01").first()
    assert item is not None
    assert item.field_values[0].value == "10.0.0.10"
    assert item.version == 1


def test_required_field_validation_blocks_creation(client, benutzer_user, server_type):
    """IP-Adresse ist Pflichtfeld - ohne sie darf nichts angelegt werden."""
    login(client, benutzer_user.username)

    resp = client.post(f"/items/new/{server_type.id}", data={"name": "ohne-ip"})

    assert resp.status_code == 200
    assert "erforderlich".encode() in resp.data
    assert ConfigItem.query.filter_by(name="ohne-ip").first() is None


def test_update_config_item_creates_change_log_entry(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    item = ConfigItem.query.filter_by(name="web01").first()

    client.post(
        f"/items/{item.id}/edit",
        data={"name": "web01", "version": str(item.version), f"field_{ip_field_id}": "10.0.0.99"},
        follow_redirects=True,
    )

    updated = db.session.get(ConfigItem, item.id)
    assert updated.field_values[0].value == "10.0.0.99"
    assert updated.version == 2
    entries = ChangeLogEntry.query.filter_by(config_item_id=item.id).all()
    assert any(e.old_value == "10.0.0.10" and e.new_value == "10.0.0.99" for e in entries)


def test_archive_by_benutzer_reactivate_requires_admin(client, benutzer_user, admin_user, server_type):
    """Archivieren dürfen Benutzer und Admin, Reaktivieren ist an die Admin-Berechtigung "löschen" angelehnt - keine eigene Zeile in der RBAC-Matrix."""
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    item = ConfigItem.query.filter_by(name="web01").first()

    client.post(f"/items/{item.id}/archive", follow_redirects=True)
    assert db.session.get(ConfigItem, item.id).is_archived is True

    # Benutzer darf nicht reaktivieren.
    resp = client.post(f"/items/{item.id}/unarchive")
    assert resp.status_code == 403
    assert db.session.get(ConfigItem, item.id).is_archived is True

    client.get("/auth/logout")
    login(client, admin_user.username)
    client.post(f"/items/{item.id}/unarchive", follow_redirects=True)
    assert db.session.get(ConfigItem, item.id).is_archived is False


def test_search_finds_item_by_field_value(client, benutzer_user, server_type):
    """Volltextsuche durchsucht auch Attributwerte, nicht nur den Namen."""
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.post(f"/items/new/{server_type.id}", data={"name": "db01", f"field_{ip_field_id}": "10.0.0.20"})

    resp = client.get("/items/?q=10.0.0.20")

    # >name< statt nur "name": die Flash-Meldung "web01 wurde angelegt" enthält
    # sonst beide Namen als Text - es geht um die tatsächliche Ergebnistabelle.
    assert b">db01<" in resp.data
    assert b">web01<" not in resp.data
