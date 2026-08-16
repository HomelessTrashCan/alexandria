from datetime import datetime, timezone

from backend.app.extensions import db
from domain.ci_status import ConfigItemStatus


class ConfigItem(db.Model):
    __tablename__ = "config_items"

    id = db.Column(db.Integer, primary_key=True)
    config_item_type_id = db.Column(db.Integer, db.ForeignKey("config_item_types.id"), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False, default=ConfigItemStatus.ACTIVE)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    config_item_type = db.relationship("ConfigItemType", back_populates="items")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    field_values = db.relationship("FieldValue", back_populates="config_item", cascade="all, delete-orphan")
    change_log_entries = db.relationship(
        "ChangeLogEntry",
        back_populates="config_item",
        cascade="all, delete-orphan",
        order_by="ChangeLogEntry.changed_at.desc()",
    )
    outgoing_relationships = db.relationship(
        "ConfigItemRelationship",
        foreign_keys="ConfigItemRelationship.source_id",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    incoming_relationships = db.relationship(
        "ConfigItemRelationship",
        foreign_keys="ConfigItemRelationship.target_id",
        back_populates="target",
        cascade="all, delete-orphan",
    )

    @property
    def is_archived(self) -> bool:
        return self.status == ConfigItemStatus.ARCHIVED

    def __repr__(self) -> str:
        return f"<ConfigItem {self.name!r}>"
