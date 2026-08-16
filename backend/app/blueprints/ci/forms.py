from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from domain.relationship_types import RelationshipType


class ConfigItemNameForm(FlaskForm):
    """Bildet nur den Namen + CSRF-Schutz ab; die dynamischen Attribute werden
    serverseitig anhand der Felddefinitionen des jeweiligen CI-Typs geprüft
    (siehe backend/app/services/config_items.py), da sie erst zur Laufzeit
    bekannt sind und sich nicht als statische WTForms-Felder deklarieren lassen.
    """

    name = StringField("Name", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Speichern")


class RelationshipForm(FlaskForm):
    target_id = SelectField("Ziel-Objekt", coerce=int, validators=[DataRequired()])
    relationship_type = SelectField(
        "Beziehungstyp",
        choices=[(value, RelationshipType.LABELS[value]) for value in RelationshipType.ALL],
        validators=[DataRequired()],
    )
    submit = SubmitField("Verknüpfen")
