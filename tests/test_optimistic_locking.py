"""Tests für optimistisches Sperren."""

from backend.app.extensions import db
from backend.app.models import ConfigItem
from tests.conftest import login


def _ip_field_id(server_type):
    return next(f.id for f in server_type.fields if f.name == "IP-Adresse")


def test_concurrent_edit_conflict_is_detected(client, benutzer_user, server_type):
    """Zwei Fenster öffnen dasselbe Formular, Fenster A speichert zuerst - Fenster B darf As Änderung nicht überschreiben."""
    login(client, benutzer_user.username)
    ip_field_id = _ip_field_id(server_type)
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()
    assert item.version == 1

    # Fenster A speichert zuerst.
    client.post(f"/items/{item.id}/edit", data={"name": "web01", "version": "1", f"field_{ip_field_id}": "10.0.0.2"})

    # Fenster B, immer noch auf Stand version=1, versucht ebenfalls zu speichern.
    resp = client.post(
        f"/items/{item.id}/edit",
        data={"name": "web01", "version": "1", f"field_{ip_field_id}": "10.0.0.99-von-B"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "zwischenzeitlich".encode() in resp.data

    current = db.session.get(ConfigItem, item.id)
    assert current.version == 2
    assert current.field_values[0].value == "10.0.0.2"  # A's Wert, nicht von B überschrieben


def test_edit_succeeds_after_reloading_current_version(client, benutzer_user, server_type):
    """Nach einem abgelehnten Speicherversuch kann derselbe Benutzer mit der
    aktuellen Version erneut speichern."""
    login(client, benutzer_user.username)
    ip_field_id = _ip_field_id(server_type)
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()
    client.post(f"/items/{item.id}/edit", data={"name": "web01", "version": "1", f"field_{ip_field_id}": "10.0.0.2"})

    resp = client.post(
        f"/items/{item.id}/edit",
        data={"name": "web01", "version": "2", f"field_{ip_field_id}": "10.0.0.3"},
        follow_redirects=True,
    )

    assert "wurde aktualisiert".encode() in resp.data
    current = db.session.get(ConfigItem, item.id)
    assert current.version == 3
    assert current.field_values[0].value == "10.0.0.3"


def test_archiving_also_increments_version(client, admin_user, server_type):
    """Nicht nur Bearbeiten, auch Archivieren zählt als Änderung des Objekts."""
    login(client, admin_user.username)
    ip_field_id = _ip_field_id(server_type)
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()

    client.post(f"/items/{item.id}/archive")

    assert db.session.get(ConfigItem, item.id).version == 2
