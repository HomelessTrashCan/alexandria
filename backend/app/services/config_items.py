import json
from datetime import datetime

from sqlalchemy.exc import IntegrityError, OperationalError

from backend.app.extensions import db
from backend.app.models import ChangeLogEntry, ConfigItem, ConfigItemRelationship, FieldDefinition, FieldValue
from domain.change_actions import ChangeAction
from domain.ci_status import ConfigItemStatus
from domain.field_types import FieldType
from domain.relationship_types import RelationshipType


class ConcurrentModificationError(Exception):
    """Ausgelöst, wenn das Konfigurationselement seit dem Öffnen des Formulars von jemand anderem geändert wurde."""


class DuplicateRelationshipError(Exception):
    """Ausgelöst, wenn dieselbe Beziehung (Quelle, Ziel, Typ) schon existiert."""


class SelfReferenceError(Exception):
    """Ausgelöst, wenn ein Konfigurationselement mit sich selbst verknüpft werden soll."""


def validate_field_values(field_definitions: list[FieldDefinition], form_data) -> tuple[dict[int, str], dict[int, str]]:
    """Prüft die eingegebenen Attributwerte gegen ihre Felddefinition.

    Rückgabe: (Werte pro Feld-ID, Fehlermeldungen pro Feld-ID).
    """
    values: dict[int, str] = {}
    errors: dict[int, str] = {}

    for field in field_definitions:
        key = f"field_{field.id}"
        if field.field_type == FieldType.BOOLEAN:
            raw = "true" if form_data.get(key) == "on" else "false"
        else:
            raw = (form_data.get(key) or "").strip()

        if field.required and not raw:
            errors[field.id] = "Dieses Feld ist erforderlich."
            continue

        if raw and field.field_type == FieldType.NUMBER:
            try:
                float(raw.replace(",", "."))
            except ValueError:
                errors[field.id] = "Bitte eine Zahl eingeben."
                continue

        if raw and field.field_type == FieldType.DATE:
            try:
                datetime.strptime(raw, "%Y-%m-%d")
            except ValueError:
                errors[field.id] = "Bitte ein Datum im Format JJJJ-MM-TT eingeben."
                continue

        if raw and field.field_type == FieldType.SELECT:
            options = json.loads(field.options or "[]")
            if raw not in options:
                errors[field.id] = "Ungültige Auswahl."
                continue

        values[field.id] = raw

    return values, errors


def create_config_item(config_item_type, name: str, field_definitions, form_data, user) -> ConfigItem:
    values, _errors = validate_field_values(field_definitions, form_data)

    item = ConfigItem(config_item_type_id=config_item_type.id, name=name, created_by_id=user.id)
    db.session.add(item)
    db.session.flush()  # item.id wird für Feldwerte und Log-Eintrag benötigt

    for field in field_definitions:
        value = values.get(field.id)
        if value:
            db.session.add(FieldValue(config_item_id=item.id, field_definition_id=field.id, value=value))

    db.session.add(ChangeLogEntry(config_item_id=item.id, action=ChangeAction.CREATED, new_value=name, changed_by_id=user.id))
    db.session.commit()
    return item


def update_config_item(item: ConfigItem, name: str, field_definitions, form_data, user, expected_version: int) -> None:
    """Aktualisiert das Konfigurationselement, sofern es seit dem Laden des Formulars nicht von jemand anderem geändert wurde (optimistisches Sperren über expected_version)."""
    if item.version != expected_version:
        raise ConcurrentModificationError(
            f'"{item.name}" wurde zwischenzeitlich von einer anderen Person geändert. '
            "Bitte die aktuelle Version prüfen und die Änderung bei Bedarf erneut vornehmen."
        )

    values, _errors = validate_field_values(field_definitions, form_data)
    changes: list[ChangeLogEntry] = []

    if item.name != name:
        changes.append(
            ChangeLogEntry(config_item_id=item.id, action=ChangeAction.UPDATED, old_value=item.name, new_value=name, changed_by_id=user.id)
        )
        item.name = name

    existing_by_field = {fv.field_definition_id: fv for fv in item.field_values}
    for field in field_definitions:
        new_value = values.get(field.id, "")
        existing = existing_by_field.get(field.id)
        old_value = existing.value if existing else None
        if (old_value or "") == (new_value or ""):
            continue

        if existing is None:
            db.session.add(FieldValue(config_item_id=item.id, field_definition_id=field.id, value=new_value))
        else:
            existing.value = new_value

        changes.append(
            ChangeLogEntry(
                config_item_id=item.id,
                action=ChangeAction.UPDATED,
                field_definition_id=field.id,
                old_value=old_value,
                new_value=new_value,
                changed_by_id=user.id,
            )
        )

    item.version += 1
    db.session.add_all(changes)
    db.session.commit()


def set_archived(item: ConfigItem, archived: bool, user) -> None:
    item.status = ConfigItemStatus.ARCHIVED if archived else ConfigItemStatus.ACTIVE
    item.version += 1
    action = ChangeAction.ARCHIVED if archived else ChangeAction.UNARCHIVED
    db.session.add(ChangeLogEntry(config_item_id=item.id, action=action, changed_by_id=user.id))
    db.session.commit()


def delete_config_item(item: ConfigItem) -> None:
    db.session.delete(item)
    db.session.commit()


def add_relationship(source: ConfigItem, target: ConfigItem, relationship_type: str, user) -> ConfigItemRelationship:
    if source.id == target.id:
        raise SelfReferenceError("Ein Konfigurationselement kann nicht mit sich selbst verknüpft werden.")

    relationship = ConfigItemRelationship(source_id=source.id, target_id=target.id, relationship_type=relationship_type, created_by_id=user.id)
    db.session.add(relationship)
    db.session.add(
        ChangeLogEntry(
            config_item_id=source.id,
            action=ChangeAction.RELATIONSHIP_ADDED,
            new_value=f"{relationship_type} -> {target.name}",
            changed_by_id=user.id,
        )
    )
    try:
        db.session.commit()
    except (IntegrityError, OperationalError):
        # IntegrityError = Duplikat, OperationalError = MariaDB meldet CHECK-Verletzungen so statt als IntegrityError.
        db.session.rollback()
        label = RelationshipType.LABELS.get(relationship_type, relationship_type)
        raise DuplicateRelationshipError(f'Die Beziehung "{label}" zu "{target.name}" existiert bereits.') from None
    return relationship


def remove_relationship(relationship: ConfigItemRelationship, user) -> None:
    db.session.add(
        ChangeLogEntry(
            config_item_id=relationship.source_id,
            action=ChangeAction.RELATIONSHIP_REMOVED,
            old_value=f"{relationship.relationship_type} -> {relationship.target.name}",
            changed_by_id=user.id,
        )
    )
    db.session.delete(relationship)
    db.session.commit()


def search_config_items(query_text: str | None = None, type_id: int | None = None, status: str | None = None, sort: str = "name"):
    query = ConfigItem.query

    if type_id:
        query = query.filter(ConfigItem.config_item_type_id == type_id)
    if status:
        query = query.filter(ConfigItem.status == status)
    if query_text:
        pattern = f"%{query_text}%"
        query = query.outerjoin(FieldValue).filter(db.or_(ConfigItem.name.ilike(pattern), FieldValue.value.ilike(pattern))).distinct()

    if sort == "created_at":
        query = query.order_by(ConfigItem.created_at.desc())
    elif sort == "type":
        query = query.join(ConfigItem.config_item_type).order_by(db.text("config_item_types.name"), ConfigItem.name)
    else:
        query = query.order_by(ConfigItem.name.asc())

    return query
