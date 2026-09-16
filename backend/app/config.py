import os


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Prüft jede Verbindung vor Gebrauch und ersetzt tote (nach DB-Neustart, "server has gone away" o. Ä.).
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    MAIL_SERVER = os.environ.get("MAIL_SERVER") or None
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Gültigkeitsdauer (Sekunden) für E-Mail-Bestätigungs- und Passwort-Reset-Links.
    TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24

    # Token-Authentifizierung für die REST-API.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 Stunden


class TestConfig(Config):
    """Konfiguration für die pytest-Suite: eigene Datenbank (cmdb_test), CSRF deaktiviert (der Testclient ist kein echter Browser)."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "mysql+pymysql://cmdb_user:cmdb_password@127.0.0.1:3306/cmdb_test"
    )
    MAIL_SERVER = None
