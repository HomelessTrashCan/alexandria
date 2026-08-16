from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from backend.app.models import User


class RegistrationForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired(), Length(min=3, max=64)])
    first_name = StringField("Vorname", validators=[DataRequired(), Length(max=64)])
    last_name = StringField("Nachname", validators=[DataRequired(), Length(max=64)])
    email = StringField("E-Mailadresse", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Kennwort", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Kennwort bestätigen", validators=[DataRequired(), EqualTo("password", message="Kennwörter stimmen nicht überein.")]
    )
    submit = SubmitField("Registrieren")

    def validate_username(self, field: StringField) -> None:
        if User.query.filter_by(username=field.data).first() is not None:
            raise ValidationError("Dieser Benutzername ist bereits vergeben.")

    def validate_email(self, field: StringField) -> None:
        if User.query.filter_by(email=field.data).first() is not None:
            raise ValidationError("Diese E-Mailadresse ist bereits registriert.")


class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired()])
    password = PasswordField("Kennwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")


class RequestPasswordResetForm(FlaskForm):
    email = StringField("E-Mailadresse", validators=[DataRequired(), Email()])
    submit = SubmitField("Kennwort zurücksetzen")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Neues Kennwort", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Kennwort bestätigen", validators=[DataRequired(), EqualTo("password", message="Kennwörter stimmen nicht überein.")]
    )
    submit = SubmitField("Kennwort speichern")
