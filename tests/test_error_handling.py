"""Tests für die Fehlerbehandlung bei nicht erreichbarer Datenbank.

Nutzt eine eigene Flask-App-Instanz mit garantiert unerreichbarer Datenbank-
URL statt der gemeinsamen app-Fixture, da hier der Ausfall simuliert wird.
"""

from backend.app import create_app
from backend.app.config import TestConfig


class UnreachableDatabaseConfig(TestConfig):
    # Port 1 hat garantiert keinen Listener -> sofortige Verbindungsverweigerung statt eines langen Timeouts.
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://cmdb_user:cmdb_password@127.0.0.1:1/cmdb_test"


def test_web_route_shows_friendly_error_when_database_is_unreachable():
    broken_app = create_app(UnreachableDatabaseConfig)
    client = broken_app.test_client()

    resp = client.post("/auth/login", data={"username": "irgendwer", "password": "irgendwas"})

    assert resp.status_code == 503
    assert "nicht erreichbar".encode() in resp.data


def test_api_route_returns_json_error_when_database_is_unreachable():
    broken_app = create_app(UnreachableDatabaseConfig)
    client = broken_app.test_client()

    resp = client.post("/api/auth/login", json={"username": "irgendwer", "password": "irgendwas"})

    assert resp.status_code == 503
    assert "nicht erreichbar" in resp.get_json()["error"]
