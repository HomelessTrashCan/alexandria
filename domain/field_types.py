"""Unterstützte Feldtypen für benutzerdefinierte Attribute."""


class FieldType:
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
    IPV4 = "ipv4"
    IPV6 = "ipv6"

    ALL = (TEXT, NUMBER, DATE, BOOLEAN, SELECT, IPV4, IPV6)

    LABELS = {
        TEXT: "Text",
        NUMBER: "Zahl",
        DATE: "Datum",
        BOOLEAN: "Wahrheitswert",
        SELECT: "Auswahlliste",
        IPV4: "IPv4-Adresse",
        IPV6: "IPv6-Adresse",
    }
