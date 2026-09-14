"""Benutzerverwaltung für Administratoren: Konten anlegen/löschen, Rollen zuweisen, (de)aktivieren."""

from sqlalchemy.exc import IntegrityError

from backend.app.extensions import db
from backend.app.models import User


class SelfManagementError(Exception):
    """Eine administrierende Person darf die eigene Rolle, den eigenen Aktiv-Status oder das eigene Konto nicht selbst ändern/löschen - sonst könnte sie sich mit einem Klick aussperren."""


def create_user(username: str, first_name: str, last_name: str, email: str, password: str, role: str) -> User:
    """Legt ein Konto direkt an, ohne den Umweg über die Selbstregistrierung.

    email_verified bleibt False: auch ein von einer administrierenden Person
    angelegtes Konto muss die E-Mailadresse bestätigen, bevor es nutzbar ist -
    dieselbe Regel wie bei der Selbstregistrierung.
    """
    user = User(username=username, first_name=first_name, last_name=last_name, email=email, role=role, email_verified=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


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


def delete_user(target_user: User, acting_user: User) -> tuple[bool, str | None]:
    """Löscht ein Konto endgültig, sofern es nicht mehr referenziert wird
    (ConfigItem.created_by, ChangeLogEntry.changed_by u. Ä.) - ein Konto, das
    bereits Konfigurationselemente erstellt oder Änderungen vorgenommen hat,
    lässt sich damit nicht löschen, ohne die Audit-Historie zu beschädigen."""
    if target_user.id == acting_user.id:
        raise SelfManagementError("Das eigene Konto kann nicht selbst gelöscht werden. Bitte eine andere administrierende Person darum bitten.")

    try:
        db.session.delete(target_user)
        db.session.commit()
        return True, None
    except IntegrityError:
        db.session.rollback()
        return False, "Dieses Konto kann nicht gelöscht werden, da es noch mit vorhandenen Konfigurationselementen oder Änderungen verknüpft ist. Bitte stattdessen deaktivieren."
