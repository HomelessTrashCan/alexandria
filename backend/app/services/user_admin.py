"""Benutzerverwaltung fuer Administratoren: Rollen zuweisen, Konten
(de)aktivieren (docs/toDo.md).
"""

from backend.app.extensions import db
from backend.app.models import User


class SelfManagementError(Exception):
    """Eine administrierende Person darf die eigene Rolle oder den eigenen
    Aktiv-Status nicht ueber diese Oberflaeche aendern.

    Grund: der user_loader (backend/app/__init__.py) behandelt ein
    deaktiviertes Konto sofort als abgemeldet - wuerde man sich selbst
    deaktivieren oder die eigene Admin-Rolle entziehen, waere man noch
    innerhalb desselben Klicks ausgesperrt und koennte den Fehler nicht
    einmal rueckgaengig machen. Eine andere administrierende Person muss das
    stattdessen uebernehmen.
    """


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
