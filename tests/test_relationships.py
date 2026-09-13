"""Tests für Beziehungen zwischen Konfigurationselementen."""

import pytest

from backend.app.models import ConfigItem, ConfigItemRelationship
from backend.app.services.config_items import SelfReferenceError, add_relationship
from tests.conftest import login


def _create_item(client, server_type, ip_field_id, name, ip):
    client.post(f"/items/new/{server_type.id}", data={"name": name, f"field_{ip_field_id}": ip})
    return ConfigItem.query.filter_by(name=name).first()


def test_add_relationship_between_items(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    source = _create_item(client, server_type, ip_field_id, "web01", "10.0.0.10")
    target = _create_item(client, server_type, ip_field_id, "db01", "10.0.0.20")

    client.post(f"/items/{source.id}/relationships", data={"target_id": str(target.id), "relationship_type": "depends_on"}, follow_redirects=True)

    rel = ConfigItemRelationship.query.filter_by(source_id=source.id, target_id=target.id).first()
    assert rel is not None
    assert rel.relationship_type == "depends_on"


def test_duplicate_relationship_is_rejected_gracefully(client, benutzer_user, server_type):
    """DB-Unique-Constraint (source, target, type) + saubere Fehlermeldung statt 500er."""
    login(client, benutzer_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    source = _create_item(client, server_type, ip_field_id, "web01", "10.0.0.10")
    target = _create_item(client, server_type, ip_field_id, "db01", "10.0.0.20")
    client.post(f"/items/{source.id}/relationships", data={"target_id": str(target.id), "relationship_type": "depends_on"})

    resp = client.post(
        f"/items/{source.id}/relationships",
        data={"target_id": str(target.id), "relationship_type": "depends_on"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert "existiert bereits".encode() in resp.data
    assert ConfigItemRelationship.query.filter_by(source_id=source.id, target_id=target.id).count() == 1


def test_self_reference_relationship_is_rejected(client, benutzer_user, server_type):
    """Über die Web-UI nicht erreichbar (Ziel-Dropdown schliesst das Objekt selbst aus), aber die Service-Funktion muss es trotzdem klar ablehnen."""
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    login(client, benutzer_user.username)
    item = _create_item(client, server_type, ip_field_id, "web01", "10.0.0.10")

    with pytest.raises(SelfReferenceError):
        add_relationship(item, item, "connected_to", benutzer_user)


def test_remove_relationship_twice_is_idempotent(client, benutzer_user, server_type):
    """Doppeltes Entfernen derselben Beziehung ergibt eine Info-Meldung statt 404."""
    login(client, benutzer_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    source = _create_item(client, server_type, ip_field_id, "web01", "10.0.0.10")
    target = _create_item(client, server_type, ip_field_id, "db01", "10.0.0.20")
    client.post(f"/items/{source.id}/relationships", data={"target_id": str(target.id), "relationship_type": "depends_on"})
    rel = ConfigItemRelationship.query.filter_by(source_id=source.id, target_id=target.id).first()

    resp_a = client.post(f"/items/{source.id}/relationships/{rel.id}/delete", follow_redirects=True)
    assert "wurde entfernt".encode() in resp_a.data

    resp_b = client.post(f"/items/{source.id}/relationships/{rel.id}/delete", follow_redirects=True)
    assert resp_b.status_code == 200
    assert "bereits entfernt".encode() in resp_b.data
