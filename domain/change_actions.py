"""Ereignisarten in der Änderungshistorie (Audit-Trail)."""


class ChangeAction:
    CREATED = "created"
    UPDATED = "updated"
    ARCHIVED = "archived"
    UNARCHIVED = "unarchived"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"

    LABELS = {
        CREATED: "Erstellt",
        UPDATED: "Geändert",
        ARCHIVED: "Archiviert",
        UNARCHIVED: "Reaktiviert",
        RELATIONSHIP_ADDED: "Beziehung hinzugefügt",
        RELATIONSHIP_REMOVED: "Beziehung entfernt",
    }
