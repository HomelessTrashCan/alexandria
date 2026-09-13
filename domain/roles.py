"""Benutzerrollen der CMDB."""


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


# Rolle, die ein neu registriertes Konto standardmässig erhält.
DEFAULT_ROLE = Role.BENUTZER
