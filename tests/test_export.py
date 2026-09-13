"""Tests für den CSV-/PDF-Export von Konfigurationselementen."""

from tests.conftest import login


def _field_id(server_type, name: str) -> int:
    return next(f.id for f in server_type.fields if f.name == name)


def test_csv_export_contains_item_name_and_field_value(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})

    resp = client.get("/items/export/csv")

    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="konfigurationselemente.csv"'
    # utf-8-sig: BOM am Anfang, daher über .decode("utf-8-sig") statt eines rohen .decode() prüfen.
    body = resp.data.decode("utf-8-sig")
    assert "web01" in body
    assert "10.0.0.10" in body


def test_csv_export_respects_active_search_filter(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})
    client.post(f"/items/new/{server_type.id}", data={"name": "db01", f"field_{ip_field_id}": "10.0.0.20"})

    resp = client.get("/items/export/csv?q=db01")

    body = resp.data.decode("utf-8-sig")
    assert "db01" in body
    assert "web01" not in body


def test_pdf_export_returns_valid_pdf_document(client, benutzer_user, server_type):
    login(client, benutzer_user.username)
    ip_field_id = _field_id(server_type, "IP-Adresse")
    client.post(f"/items/new/{server_type.id}", data={"name": "web01", f"field_{ip_field_id}": "10.0.0.10"})

    resp = client.get("/items/export/pdf")

    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    # Jede gültige PDF-Datei beginnt mit dieser Signatur.
    assert resp.data.startswith(b"%PDF")


def test_betrachter_can_export_but_anonymous_cannot(client, betrachter_user, server_type):
    resp = client.get("/items/export/csv")
    assert resp.status_code == 302  # nicht angemeldet -> Redirect zum Login

    login(client, betrachter_user.username)
    resp = client.get("/items/export/csv")
    assert resp.status_code == 200
