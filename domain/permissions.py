"""RBAC-Rechte-Matrix: welche Rolle darf welche Aktion. Neue Funktionen bekommen hier einen Eintrag, statt Rollen-Checks über Routen zu verstreuen."""

from domain.roles import Role

PERMISSIONS = {
    "config_item.create": (Role.BENUTZER, Role.ADMIN),
    "config_item.read": (Role.BENUTZER, Role.ADMIN, Role.BETRACHTER),
    "config_item.update": (Role.BENUTZER, Role.ADMIN),
    "config_item.archive": (Role.BENUTZER, Role.ADMIN),
    "config_item.delete": (Role.ADMIN,),
    "config_item.link": (Role.BENUTZER, Role.ADMIN),
    "config_item.unlink": (Role.BENUTZER, Role.ADMIN),
    "config_item.history_read": (Role.BENUTZER, Role.ADMIN, Role.BETRACHTER),
    "config_item_type.create": (Role.ADMIN,),
    "config_item_type.read": (Role.BENUTZER, Role.ADMIN, Role.BETRACHTER),
    "config_item_type.update": (Role.ADMIN,),
    "config_item_type.delete": (Role.ADMIN,),
    "field_definition.create": (Role.ADMIN,),
    "field_definition.read": (Role.BENUTZER, Role.ADMIN, Role.BETRACHTER),
    "field_definition.update": (Role.ADMIN,),
    "field_definition.archive": (Role.ADMIN,),
    "field_definition.delete": (Role.ADMIN,),
    "user.manage": (Role.ADMIN,),
}


def has_permission(role: str, action: str) -> bool:
    return role in PERMISSIONS.get(action, ())
