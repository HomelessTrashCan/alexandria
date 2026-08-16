"""Benutzerrollen der CMDB, siehe docs/claude.md, Abschnitt "Rollenmanagement"."""


class Role:
    BENUTZER = "benutzer"
    ADMIN = "admin"
    BETRACHTER = "betrachter"

    ALL = (BENUTZER, ADMIN, BETRACHTER)

    LABELS = {
        BENUTZER: "Benutzer",
        ADMIN: "Administrator",
        BETRACHTER: "Betrachter",
    }


# Rolle, die ein neu registriertes Konto per Default erhält (docs/claude.md, Zeile 22).
DEFAULT_ROLE = Role.BENUTZER
