"""Unterstuetzte Feldtypen fuer benutzerdefinierte Attribute, siehe docs/claude.md, Zeile 25."""


class FieldType:
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"

    ALL = (TEXT, NUMBER, DATE, BOOLEAN, SELECT)

    LABELS = {
        TEXT: "Text",
        NUMBER: "Zahl",
        DATE: "Datum",
        BOOLEAN: "Wahrheitswert",
        SELECT: "Auswahlliste",
    }
