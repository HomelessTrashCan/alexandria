from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app.extensions import db
from domain.roles import DEFAULT_ROLE, Role


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=DEFAULT_ROLE)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    # Deaktivierte Konten können sich nicht mehr anmelden und werden bei einer laufenden Session sofort ausgeloggt.
    active = db.Column(db.Boolean, nullable=False, default=True)
    # Wird in Passwort-Reset-Tokens eingebettet (siehe blueprints/auth/routes.py).
    # Erhöht bei jedem Passwort-Wechsel UND bei jeder neuen Reset-Anfrage -
    # macht damit sowohl einen bereits eingelösten Link ungültig als auch
    # alle älteren, noch nicht eingelösten Links, sobald ein neuer angefordert
    # wird ("zuletzt angeforderter Link gewinnt" statt "first come, first served").
    password_reset_counter = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
        self.invalidate_password_reset_tokens()

    def invalidate_password_reset_tokens(self) -> None:
        """Macht alle bisher ausgestellten Passwort-Reset-Links für dieses Konto ungültig."""
        # or 0: falls das Objekt noch nicht in der DB ist (Registrierung),
        # ist der Spalten-Default noch nicht angewendet und der Wert None.
        self.password_reset_counter = (self.password_reset_counter or 0) + 1

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def role_label(self) -> str:
        return Role.LABELS.get(self.role, self.role)

    @property
    def is_active(self) -> bool:
        """Überschreibt UserMixin.is_active (dort immer True) mit dem echten Konto-Status."""
        return self.active

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"
