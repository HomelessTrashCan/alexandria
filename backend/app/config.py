import os


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Prueft jede Verbindung aus dem Pool vor Gebrauch mit einem leichten
    # "SELECT 1" und verwirft/ersetzt sie bei Bedarf. Ohne das wuerde eine
    # DB, die kurz weg war (Neustart, Netzwerkausfall, MySQL/MariaDBs eigenes
    # "server has gone away" bei langer Inaktivitaet), noch fuer eine Weile
    # tote Verbindungen aus dem Pool ausliefern und Fehler produzieren, obwohl
    # die DB laengst wieder erreichbar ist.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    MAIL_SERVER = os.environ.get("MAIL_SERVER") or None
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "cmdb@example.com")

    # Gültigkeitsdauer (Sekunden) für E-Mail-Bestätigungs- und Passwort-Reset-Links.
    TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24

    # RESTful API: Token-Authentifizierung ohne Browser (docs/claude.md, Zeile 21).
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 Stunden


class TestConfig(Config):
    """Konfiguration fuer die pytest-Suite (siehe tests/conftest.py).

    Eigene Datenbank (cmdb_test), damit Tests niemals echte Entwicklungsdaten
    beruehren. WTF_CSRF_ENABLED=False, weil der Testclient keinen echten
    Browser simuliert und sonst jeder POST-Request erst ein CSRF-Token aus
    einem vorherigen GET extrahieren muesste - reine Testreibung ohne
    Sicherheitsgewinn, da hier ohnehin kein Cross-Site-Request-Risiko besteht.
    """

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "mysql+pymysql://cmdb_user:cmdb_password@127.0.0.1:3306/cmdb_test"
    )
    MAIL_SERVER = None
