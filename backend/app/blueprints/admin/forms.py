from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from backend.app.models import ConfigItemType, FieldDefinition
from domain.field_types import FieldType


class ConfigItemTypeForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=64)])
    description = StringField("Beschreibung", validators=[Length(max=255)])
    submit = SubmitField("Speichern")

    def __init__(self, original_name: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, field):
        if field.data == self.original_name:
            return
        if ConfigItemType.query.filter_by(name=field.data).first() is not None:
            raise ValidationError("Dieser Typname ist bereits vergeben.")


class FieldDefinitionForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=64)])
    field_type = SelectField("Feldtyp", choices=[(value, FieldType.LABELS[value]) for value in FieldType.ALL], validators=[DataRequired()])
    required = BooleanField("Pflichtfeld")
    options = StringField("Optionen (nur bei Auswahlliste, mit Komma trennen)")
    submit = SubmitField("Speichern")

    def __init__(self, config_item_type_id: int | None = None, original_name: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_item_type_id = config_item_type_id
        self.original_name = original_name

    def validate_name(self, field):
        if field.data == self.original_name or self.config_item_type_id is None:
            return
        exists = FieldDefinition.query.filter_by(config_item_type_id=self.config_item_type_id, name=field.data).first()
        if exists is not None:
            raise ValidationError("Ein Feld mit diesem Namen existiert für diesen Typ bereits.")

    def validate_options(self, field):
        if self.field_type.data == FieldType.SELECT:
            options = [option.strip() for option in (field.data or "").split(",") if option.strip()]
            if not options:
                raise ValidationError("Bitte mindestens eine Option angeben (mit Komma trennen).")
