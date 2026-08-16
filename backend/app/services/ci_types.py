import json

from sqlalchemy.exc import IntegrityError

from backend.app.extensions import db
from backend.app.models import ConfigItemType, FieldDefinition
from domain.field_types import FieldType


def create_type(name: str, description: str | None) -> ConfigItemType:
    config_item_type = ConfigItemType(name=name, description=description or None)
    db.session.add(config_item_type)
    db.session.commit()
    return config_item_type


def update_type(config_item_type: ConfigItemType, name: str, description: str | None) -> None:
    config_item_type.name = name
    config_item_type.description = description or None
    db.session.commit()


def delete_type(config_item_type: ConfigItemType) -> tuple[bool, str | None]:
    try:
        db.session.delete(config_item_type)
        db.session.commit()
        return True, None
    except IntegrityError:
        db.session.rollback()
        return False, "Dieser Typ kann nicht gelöscht werden, solange noch Konfigurationselemente dieses Typs existieren."


def next_position(config_item_type: ConfigItemType) -> int:
    return max((field.position for field in config_item_type.fields), default=0) + 1


def parse_options(raw: str) -> str | None:
    options = [option.strip() for option in (raw or "").split(",") if option.strip()]
    return json.dumps(options) if options else None


def options_to_text(options_json: str | None) -> str:
    if not options_json:
        return ""
    return ", ".join(json.loads(options_json))


def create_field(config_item_type: ConfigItemType, name: str, field_type: str, required: bool, options_raw: str) -> FieldDefinition:
    field = FieldDefinition(
        config_item_type_id=config_item_type.id,
        name=name,
        field_type=field_type,
        required=required,
        options=parse_options(options_raw) if field_type == FieldType.SELECT else None,
        position=next_position(config_item_type),
    )
    db.session.add(field)
    db.session.commit()
    return field


def update_field(field: FieldDefinition, name: str, field_type: str, required: bool, options_raw: str) -> None:
    field.name = name
    field.field_type = field_type
    field.required = required
    field.options = parse_options(options_raw) if field_type == FieldType.SELECT else None
    db.session.commit()


def set_field_archived(field: FieldDefinition, archived: bool) -> None:
    field.archived = archived
    db.session.commit()


def delete_field(field: FieldDefinition) -> None:
    db.session.delete(field)
    db.session.commit()
