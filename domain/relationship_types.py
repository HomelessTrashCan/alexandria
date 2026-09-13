"""Beziehungstypen zwischen Konfigurationselementen. Gerichtet (source -> target), damit sich Abhängigkeiten nachvollziehen lassen."""


class RelationshipType:
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    CONNECTED_TO = "connected_to"

    ALL = (DEPENDS_ON, PART_OF, CONNECTED_TO)

    LABELS = {
        DEPENDS_ON: "hängt ab von",
        PART_OF: "ist Teil von",
        CONNECTED_TO: "verbunden mit",
    }
