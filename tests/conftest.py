"""Gemeinsame pytest-Fixtures, automatisch von pytest geladen für alle Tests unter tests/."""

import os

# Muss vor jedem Import aus backend.app passieren: Config liest SECRET_KEY und
# DATABASE_URL schon beim Import aus os.environ, nicht erst bei Verwendung.
os.environ.setdefault("SECRET_KEY", "test-secret-key-thats-long-enough-for-hs256-32bytes")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://cmdb_user:cmdb_password@127.0.0.1:3306/cmdb_test")

import pytest

from backend.app import create_app
from backend.app.config import TestConfig
from backend.app.extensions import db as _db
from domain.field_types import FieldType
from domain.roles import Role


@pytest.fixture(scope="session")
def app():
    """Erstellt die Flask-App einmal pro Testlauf. Der App-Context zum Erzeugen/Entfernen des Schemas bleibt bewusst nicht über den yield hinweg offen, siehe app_context unten."""
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def app_context(app):
    """Ein frischer App-Context pro Test, nicht einer für die ganze Session.

    Flask-Login legt den eingeloggten Benutzer in flask.g ab, das am
    App-Context hängt statt am Request. Bliebe ein Context über mehrere Tests
    offen, würde current_user aus einem längst abgeschlossenen Test hängen
    bleiben, obwohl der neue Test-Client eine leere Session hat.
    """
    with app.app_context():
        yield


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_db(app_context):
    """Leert nach jedem Test alle Tabellen wieder, in umgekehrter Erstellungsreihenfolge (Kindtabellen vor Elterntabellen wegen Fremdschlüsseln)."""
    yield
    for table in reversed(_db.metadata.sorted_tables):
        _db.session.execute(table.delete())
    _db.session.commit()


@pytest.fixture
def make_user(app_context):
    """Factory statt fertigem Objekt, weil manche Tests mehrere Benutzer mit unterschiedlichen Rollen brauchen."""
    from backend.app.models import User

    def _make(username: str, role: str = Role.BENUTZER, password: str = "supersecret1") -> User:
        user = User(
            username=username,
            first_name="Test",
            last_name="User",
            email=f"{username}@example.com",
            role=role,
            email_verified=True,
        )
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        return user

    return _make


@pytest.fixture
def admin_user(make_user):
    return make_user("admin_test", Role.ADMIN)


@pytest.fixture
def benutzer_user(make_user):
    return make_user("benutzer_test", Role.BENUTZER)


@pytest.fixture
def betrachter_user(make_user):
    return make_user("betrachter_test", Role.BETRACHTER)


def login(client, username: str, password: str = "supersecret1"):
    """Meldet den Test-Client per Session-Cookie als den angegebenen Benutzer an. Kein Fixture, da sie einen Benutzernamen als Parameter braucht."""
    return client.post("/auth/login", data={"username": username, "password": password}, follow_redirects=True)


@pytest.fixture
def server_type(app_context):
    """CI-Typ 'Server' mit einem Pflichtfeld und einer Auswahlliste, spart jedem Test einen eigenen Typ."""
    from backend.app.models import ConfigItemType, FieldDefinition

    config_item_type = ConfigItemType(name="Server", description="Testtyp")
    _db.session.add(config_item_type)
    _db.session.flush()  # vergibt die ID, ohne die Transaktion abzuschliessen
    _db.session.add_all(
        [
            FieldDefinition(config_item_type_id=config_item_type.id, name="IP-Adresse", field_type=FieldType.TEXT, required=True, position=1),
            FieldDefinition(
                config_item_type_id=config_item_type.id,
                name="Betriebssystem",
                field_type=FieldType.SELECT,
                options='["Ubuntu", "Windows Server"]',
                position=2,
            ),
        ]
    )
    _db.session.commit()
    return config_item_type
