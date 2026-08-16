from backend.app.extensions import db


class FieldValue(db.Model):
    __tablename__ = "field_values"
    __table_args__ = (db.UniqueConstraint("config_item_id", "field_definition_id", name="uq_field_value_item_field"),)

    id = db.Column(db.Integer, primary_key=True)
    config_item_id = db.Column(db.Integer, db.ForeignKey("config_items.id"), nullable=False)
    field_definition_id = db.Column(db.Integer, db.ForeignKey("field_definitions.id"), nullable=False)
    value = db.Column(db.Text)

    config_item = db.relationship("ConfigItem", back_populates="field_values")
    field_definition = db.relationship("FieldDefinition", back_populates="values")

    def __repr__(self) -> str:
        return f"<FieldValue item={self.config_item_id} field={self.field_definition_id}>"
