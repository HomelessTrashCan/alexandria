from backend.app.extensions import db
from domain.field_types import FieldType


class FieldDefinition(db.Model):
    __tablename__ = "field_definitions"
    __table_args__ = (db.UniqueConstraint("config_item_type_id", "name", name="uq_field_definition_type_name"),)

    id = db.Column(db.Integer, primary_key=True)
    config_item_type_id = db.Column(db.Integer, db.ForeignKey("config_item_types.id"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    field_type = db.Column(db.String(16), nullable=False, default=FieldType.TEXT)
    required = db.Column(db.Boolean, nullable=False, default=False)
    # JSON-kodierte Liste moeglicher Werte, nur relevant wenn field_type == SELECT.
    options = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False, default=0)
    archived = db.Column(db.Boolean, nullable=False, default=False)

    config_item_type = db.relationship("ConfigItemType", back_populates="fields")
    values = db.relationship("FieldValue", back_populates="field_definition", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FieldDefinition {self.name!r} ({self.field_type})>"
