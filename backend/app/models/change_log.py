from datetime import datetime, timezone

from backend.app.extensions import db


class ChangeLogEntry(db.Model):
    __tablename__ = "change_log_entries"

    id = db.Column(db.Integer, primary_key=True)
    config_item_id = db.Column(db.Integer, db.ForeignKey("config_items.id"), nullable=False)
    # NULL bei Objekt-Ereignissen (erstellt/archiviert/...), gesetzt bei Attribut-Änderungen.
    field_definition_id = db.Column(db.Integer, db.ForeignKey("field_definitions.id"))
    action = db.Column(db.String(24), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    config_item = db.relationship("ConfigItem", back_populates="change_log_entries")
    field_definition = db.relationship("FieldDefinition")
    changed_by = db.relationship("User", foreign_keys=[changed_by_id])

    def __repr__(self) -> str:
        return f"<ChangeLogEntry {self.action} on item={self.config_item_id}>"
