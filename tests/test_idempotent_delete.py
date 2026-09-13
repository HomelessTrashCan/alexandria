"""Tests für idempotentes Löschen."""

from backend.app.models import ConfigItem, ConfigItemType, FieldDefinition
from tests.conftest import login


def test_delete_config_item_twice_is_idempotent(client, admin_user, server_type):
    login(client, admin_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()

    resp_a = client.post(f"/items/{item.id}/delete", follow_redirects=True)
    assert "endgültig gelöscht".encode() in resp_a.data

    resp_b = client.post(f"/items/{item.id}/delete", follow_redirects=True)
    assert resp_b.status_code == 200
    assert "bereits gelöscht".encode() in resp_b.data


def test_delete_type_twice_is_idempotent(client, admin_user):
    login(client, admin_user.username)
    client.post("/admin/types/new", data={"name": "Temp-Typ", "description": ""})
    config_item_type = ConfigItemType.query.filter_by(name="Temp-Typ").first()

    resp_a = client.post(f"/admin/types/{config_item_type.id}/delete", follow_redirects=True)
    assert "wurde gelöscht".encode() in resp_a.data

    resp_b = client.post(f"/admin/types/{config_item_type.id}/delete", follow_redirects=True)
    assert resp_b.status_code == 200
    assert "bereits gelöscht".encode() in resp_b.data


def test_delete_field_twice_is_idempotent(client, admin_user, server_type):
    login(client, admin_user.username)
    client.post(f"/admin/types/{server_type.id}/fields/new", data={"name": "Temp-Feld", "field_type": "text", "required": ""})
    field = FieldDefinition.query.filter_by(config_item_type_id=server_type.id, name="Temp-Feld").first()

    resp_a = client.post(f"/admin/types/{server_type.id}/fields/{field.id}/delete", follow_redirects=True)
    assert "endgültig gelöscht".encode() in resp_a.data

    resp_b = client.post(f"/admin/types/{server_type.id}/fields/{field.id}/delete", follow_redirects=True)
    assert resp_b.status_code == 200
    assert "bereits gelöscht".encode() in resp_b.data


def test_delete_field_with_mismatched_type_id_stays_a_real_404(client, admin_user, server_type):
    """Die Typ-Zugehörigkeits-Prüfung ist keine Race Condition, sondern eine URL-Integritätsprüfung - bleibt ein echter 404."""
    login(client, admin_user.username)
    other_type = ConfigItemType(name="Anderer-Typ")
    from backend.app.extensions import db

    db.session.add(other_type)
    db.session.commit()
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")

    resp = client.post(f"/admin/types/{other_type.id}/fields/{ip_field_id}/delete")

    assert resp.status_code == 404
