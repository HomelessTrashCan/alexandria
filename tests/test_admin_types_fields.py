"""Tests für die Admin-Oberfläche zur Verwaltung von CI-Typen und Felddefinitionen."""

import json

from backend.app.models import ConfigItemType, FieldDefinition
from tests.conftest import login


def test_create_type_with_select_field(client, admin_user):
    login(client, admin_user.username)
    client.post("/admin/types/new", data={"name": "Lizenz", "description": "Softwarelizenzen"})
    config_item_type = ConfigItemType.query.filter_by(name="Lizenz").first()

    resp = client.post(
        f"/admin/types/{config_item_type.id}/fields/new",
        data={"name": "Hersteller", "field_type": "select", "options": "Microsoft, Adobe, JetBrains", "required": "y"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    field = FieldDefinition.query.filter_by(config_item_type_id=config_item_type.id, name="Hersteller").first()
    assert field.required is True
    assert json.loads(field.options) == ["Microsoft", "Adobe", "JetBrains"]


def test_duplicate_type_name_is_rejected(client, admin_user, server_type):
    login(client, admin_user.username)

    resp = client.post("/admin/types/new", data={"name": server_type.name, "description": "Duplikat"})

    assert "bereits vergeben".encode() in resp.data
    assert ConfigItemType.query.filter_by(name=server_type.name).count() == 1


def test_select_field_without_options_is_rejected(client, admin_user, server_type):
    login(client, admin_user.username)

    resp = client.post(
        f"/admin/types/{server_type.id}/fields/new",
        data={"name": "Kaputt", "field_type": "select", "options": ""},
        follow_redirects=True,
    )

    assert "mindestens eine Option".encode() in resp.data
    assert FieldDefinition.query.filter_by(config_item_type_id=server_type.id, name="Kaputt").first() is None


def test_archived_field_disappears_from_new_item_form_but_keeps_existing_values(client, admin_user, server_type):
    login(client, admin_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    os_field_id = next(f.id for f in server_type.fields if f.name == "Betriebssystem")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1", f"field_{os_field_id}": "Ubuntu"})
    from backend.app.models import ConfigItem

    item = ConfigItem.query.filter_by(name="web01").first()

    client.post(f"/admin/types/{server_type.id}/fields/{os_field_id}/archive")

    # Nicht auf den blossen Text "Betriebssystem" prüfen - der taucht auch in
    # der Flash-Meldung auf. Stattdessen das Formularfeld selbst prüfen.
    new_form_resp = client.get(f"/items/new/{server_type.id}")
    assert f'field_{os_field_id}'.encode() not in new_form_resp.data

    detail_resp = client.get(f"/items/{item.id}")
    assert b"Ubuntu" in detail_resp.data


def test_delete_type_blocked_while_items_exist(client, admin_user, server_type):
    """type_service.delete_type fängt die FK-Verletzung ab und zeigt eine verständliche Meldung statt eines 500ers."""
    login(client, admin_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})

    resp = client.post(f"/admin/types/{server_type.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert "kann nicht gelöscht werden".encode() in resp.data
    assert ConfigItemType.query.filter_by(id=server_type.id).count() == 1
