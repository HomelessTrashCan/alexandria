from datetime import datetime, timezone

from backend.app.extensions import db


class ConfigItemType(db.Model):
    __tablename__ = "config_item_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    fields = db.relationship(
        "FieldDefinition",
        back_populates="config_item_type",
        order_by="FieldDefinition.position",
        cascade="all, delete-orphan",
    )
    items = db.relationship("ConfigItem", back_populates="config_item_type")

    def __repr__(self) -> str:
        return f"<ConfigItemType {self.name!r}>"
