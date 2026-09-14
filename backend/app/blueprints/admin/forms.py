from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from backend.app.models import ConfigItemType, FieldDefinition, User
from domain.field_types import FieldType
from domain.roles import Role


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


class CreateUserForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired(), Length(min=3, max=64)])
    first_name = StringField("Vorname", validators=[DataRequired(), Length(max=64)])
    last_name = StringField("Nachname", validators=[DataRequired(), Length(max=64)])
    email = StringField("E-Mailadresse", validators=[DataRequired(), Email(), Length(max=255)])
    role = SelectField("Rolle", choices=[(value, Role.LABELS[value]) for value in Role.ALL], validators=[DataRequired()])
    password = PasswordField("Kennwort", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Kennwort bestätigen", validators=[DataRequired(), EqualTo("password", message="Kennwörter stimmen nicht überein.")]
    )
    submit = SubmitField("Konto anlegen")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first() is not None:
            raise ValidationError("Dieser Benutzername ist bereits vergeben.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is not None:
            raise ValidationError("Diese E-Mailadresse ist bereits registriert.")
