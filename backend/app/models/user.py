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
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

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
