"""Tests für die Rechte-Matrix.

Keine vollständige Kombinatorik, sondern die Grenzfälle, die am ehesten falsch
programmiert werden: die schwächste Rolle darf nicht mehr als erlaubt, die
stärkste darf alles.
"""

from backend.app.models import ConfigItem
from tests.conftest import login


def test_betrachter_can_read_but_not_create(client, betrachter_user, server_type):
    login(client, betrachter_user.username)

    assert client.get("/items/").status_code == 200
    assert client.get(f"/items/new/{server_type.id}").status_code == 403


def test_betrachter_cannot_delete_or_manage_admin_area(client, betrachter_user, server_type):
    login(client, betrachter_user.username)

    assert client.post(f"/admin/types/{server_type.id}/delete").status_code == 403
    assert client.get("/admin/types/new").status_code == 403


def test_benutzer_can_create_but_not_delete_config_item(client, benutzer_user, server_type):
    """Löschen ist Admin-only, archivieren/erstellen dürfen Benutzer und Admin."""
    login(client, benutzer_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()
    assert item is not None

    resp = client.post(f"/items/{item.id}/delete")
    assert resp.status_code == 403
    assert ConfigItem.query.filter_by(name="web01").first() is not None


def test_benutzer_cannot_manage_field_definitions(client, benutzer_user, server_type):
    """Felddefinitionen sind laut RBAC-Matrix komplett Admin-only (auch Erstellen)."""
    login(client, benutzer_user.username)

    resp = client.post(f"/admin/types/{server_type.id}/fields/new", data={"name": "Neu", "field_type": "text", "required": ""})

    assert resp.status_code == 403


def test_admin_can_do_everything_a_benutzer_and_more(client, admin_user, server_type):
    login(client, admin_user.username)
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.1"})
    item = ConfigItem.query.filter_by(name="web01").first()

    resp = client.post(f"/items/{item.id}/delete", follow_redirects=True)

    assert resp.status_code == 200
    assert ConfigItem.query.filter_by(name="web01").first() is None


def test_anonymous_user_is_redirected_to_login(client):
    resp = client.get("/items/")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
