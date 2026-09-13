"""Benutzerverwaltung für Administratoren: Rollen zuweisen, Konten (de)aktivieren."""

from backend.app.extensions import db
from backend.app.models import User


class SelfManagementError(Exception):
    """Eine administrierende Person darf die eigene Rolle oder den eigenen Aktiv-Status nicht selbst ändern - sonst könnte sie sich mit einem Klick aussperren."""


def update_role(target_user: User, new_role: str, acting_user: User) -> None:
    if target_user.id == acting_user.id:
        raise SelfManagementError("Die eigene Rolle kann nicht selbst geändert werden. Bitte eine andere administrierende Person darum bitten.")
    target_user.role = new_role
    db.session.commit()


def set_active(target_user: User, active: bool, acting_user: User) -> None:
    if target_user.id == acting_user.id:
        raise SelfManagementError("Das eigene Konto kann nicht selbst deaktiviert werden. Bitte eine andere administrierende Person darum bitten.")
    target_user.active = active
    db.session.commit()
