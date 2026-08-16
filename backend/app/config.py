import os


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
