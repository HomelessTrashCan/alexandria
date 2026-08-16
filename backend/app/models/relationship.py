from datetime import datetime, timezone

from backend.app.extensions import db
from domain.relationship_types import RelationshipType


class ConfigItemRelationship(db.Model):
    __tablename__ = "config_item_relationships"
    __table_args__ = (
        db.UniqueConstraint("source_id", "target_id", "relationship_type", name="uq_relationship_source_target_type"),
        db.CheckConstraint("source_id != target_id", name="ck_relationship_no_self_reference"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("config_items.id"), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey("config_items.id"), nullable=False)
    relationship_type = db.Column(db.String(32), nullable=False, default=RelationshipType.DEPENDS_ON)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    source = db.relationship("ConfigItem", foreign_keys=[source_id], back_populates="outgoing_relationships")
    target = db.relationship("ConfigItem", foreign_keys=[target_id], back_populates="incoming_relationships")
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<ConfigItemRelationship {self.source_id} -{self.relationship_type}-> {self.target_id}>"
