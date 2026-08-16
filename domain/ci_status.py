"""Status eines Konfigurationselements.

"archivieren" (Benutzer + Admin) ist der üblich zu verwendende Soft-Delete;
das echte Löschen (RBAC: nur Admin) entfernt die Zeile endgültig aus der DB.
"""


class ConfigItemStatus:
    ACTIVE = "active"
    ARCHIVED = "archived"

    LABELS = {
        ACTIVE: "Aktiv",
        ARCHIVED: "Archiviert",
    }
