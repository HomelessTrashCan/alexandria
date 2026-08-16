import json

from backend.app.models import ChangeLogEntry, ConfigItem, ConfigItemType, FieldDefinition


def serialize_field_definition(field: FieldDefinition) -> dict:
    return {
        "id": field.id,
        "name": field.name,
        "field_type": field.field_type,
        "required": field.required,
        "options": json.loads(field.options) if field.options else None,
    }


def serialize_type(config_item_type: ConfigItemType) -> dict:
    return {
        "id": config_item_type.id,
        "name": config_item_type.name,
        "description": config_item_type.description,
        "fields": [serialize_field_definition(f) for f in config_item_type.fields if not f.archived],
    }


def serialize_item(item: ConfigItem, detailed: bool = False) -> dict:
    data = {
        "id": item.id,
        "name": item.name,
        "type": item.config_item_type.name,
        "type_id": item.config_item_type_id,
        "status": item.status,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
    if detailed:
        data["fields"] = {fv.field_definition.name: fv.value for fv in item.field_values}
        data["relationships"] = {
            "outgoing": [
                {"type": rel.relationship_type, "target_id": rel.target_id, "target_name": rel.target.name}
                for rel in item.outgoing_relationships
            ],
            "incoming": [
                {"type": rel.relationship_type, "source_id": rel.source_id, "source_name": rel.source.name}
                for rel in item.incoming_relationships
            ],
        }
    return data


def serialize_change(entry: ChangeLogEntry) -> dict:
    return {
        "action": entry.action,
        "field": entry.field_definition.name if entry.field_definition else None,
        "old_value": entry.old_value,
        "new_value": entry.new_value,
        "changed_by": entry.changed_by.username,
        "changed_at": entry.changed_at.isoformat(),
    }
