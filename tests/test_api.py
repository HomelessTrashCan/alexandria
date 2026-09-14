"""Tests für die REST-API (Token-Authentifizierung ohne Browser)."""

from backend.app.models import ConfigItem
from tests.conftest import login


def _get_token(client, username, password="supersecret1"):
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return resp.get_json()["access_token"]


def test_api_requires_token(client):
    resp = client.get("/api/v1/items")
    assert resp.status_code == 401


def test_api_login_returns_token_for_valid_credentials(client, benutzer_user):
    resp = client.post("/api/v1/auth/login", json={"username": benutzer_user.username, "password": "supersecret1"})

    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_api_login_rejects_wrong_password(client, benutzer_user):
    resp = client.post("/api/v1/auth/login", json={"username": benutzer_user.username, "password": "falsch"})
    assert resp.status_code == 401


def test_api_list_types_includes_field_definitions(client, benutzer_user, server_type):
    token = _get_token(client, benutzer_user.username)

    resp = client.get("/api/v1/types", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.get_json()
    server_entry = next(t for t in data if t["name"] == "Server")
    field_names = {f["name"] for f in server_entry["fields"]}
    assert "IP-Adresse" in field_names


def test_api_search_filters_by_field_value(client, benutzer_user, server_type):
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    login(client, benutzer_user.username)  # Web-Login, um über die Web-Route Testdaten anzulegen
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.post(f"/items/new/{server_type.id}", data={"name": "db01", f"field_{ip_field_id}": "10.0.0.20"})
    client.get("/auth/logout")

    token = _get_token(client, benutzer_user.username)
    resp = client.get("/api/v1/items?q=10.0.0.20", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    names = {item["name"] for item in resp.get_json()}
    assert names == {"db01"}


def test_api_item_detail_includes_relationships_and_history(client, benutzer_user, server_type):
    ip_field_id = next(f.id for f in server_type.fields if f.name == "IP-Adresse")
    login(client, benutzer_user.username)
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.post(f"/items/new/{server_type.id}", data={"name": "db01", f"field_{ip_field_id}": "10.0.0.20"})
    web01 = ConfigItem.query.filter_by(name="web01").first()
    db01 = ConfigItem.query.filter_by(name="db01").first()
    client.post(f"/items/{web01.id}/relationships", data={"target_id": str(db01.id), "relationship_type": "depends_on"})
    client.get("/auth/logout")

    token = _get_token(client, benutzer_user.username)
    resp = client.get(f"/api/v1/items/{web01.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["fields"]["IP-Adresse"] == "10.0.0.10"
    assert data["relationships"]["outgoing"][0]["target_name"] == "db01"

    history_resp = client.get(f"/api/v1/items/{web01.id}/history", headers={"Authorization": f"Bearer {token}"})
    assert history_resp.status_code == 200
    actions = {entry["action"] for entry in history_resp.get_json()}
    assert "created" in actions


def test_api_available_to_all_roles_read_only(client, betrachter_user, server_type):
    """Lesen ist laut RBAC-Matrix für alle drei Rollen erlaubt, auch über die API."""
    token = _get_token(client, betrachter_user.username)

    resp = client.get("/api/v1/items", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
