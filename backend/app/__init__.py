import json
import logging

from flask import Flask, jsonify, render_template, request
from sqlalchemy.exc import OperationalError

from backend.app.config import Config
from backend.app.extensions import db, jwt, login_manager, mail, migrate
from domain.change_actions import ChangeAction
from domain.field_types import FieldType
from domain.permissions import has_permission
from domain.relationship_types import RelationshipType
from domain.roles import Role


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ohne dies zeigt Python INFO-Meldungen (z. B. von Werkzeug oder kuenftigen
    # logger.info-Aufrufen) standardmaessig nicht an.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s in %(name)s: %(message)s")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melde dich an, um fortzufahren."
    login_manager.login_message_category = "warning"

    from backend.app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        user = db.session.get(User, int(user_id))
        # Gibt None zurueck statt des deaktivierten Kontos: Flask-Login
        # behandelt das wie "nicht angemeldet". Das beendet eine bereits
        # laufende Session sofort beim naechsten Request, sobald ein Admin
        # das Konto deaktiviert - nicht erst bei der naechsten Anmeldung.
        if user is not None and not user.active:
            return None
        return user

    from backend.app.blueprints.admin import admin_bp
    from backend.app.blueprints.api import api_bp
    from backend.app.blueprints.auth import auth_bp
    from backend.app.blueprints.ci import ci_bp
    from backend.app.blueprints.web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(ci_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    # Fuer Templates: Rechte-Checks und Enum-Konstanten direkt verfuegbar machen,
    # damit UI-Elemente (Buttons, dynamische Formularfelder) ohne Umweg pruefbar sind.
    # Die eigentliche Durchsetzung der Rechte bleibt Sache der Routen (@permission_required).
    app.jinja_env.globals["has_permission"] = has_permission
    app.jinja_env.globals["FieldType"] = FieldType
    app.jinja_env.globals["RelationshipType"] = RelationshipType
    app.jinja_env.globals["ChangeAction"] = ChangeAction
    app.jinja_env.globals["Role"] = Role
    app.jinja_env.filters["from_json"] = lambda value: json.loads(value) if value else []

    @app.errorhandler(OperationalError)
    def handle_database_unavailable(error):
        """Faengt DB-Verbindungsfehler ab (Server down, Netzwerkausfall, o.ae.),
        damit Benutzer eine verstaendliche Meldung statt eines rohen 500ers/
        Stacktrace sehen. Bewusst nur OperationalError (Verbindungs-/Betriebs-
        fehler), nicht z. B. IntegrityError - ein fehlgeschlagener Unique-
        Constraint ist ein Anwendungsfall, kein Infrastrukturausfall, und soll
        weiterhin dort behandelt werden, wo er auftritt.
        """
        app.logger.error("Datenbank nicht erreichbar: %s", error)
        if request.blueprint == "api":
            return jsonify(error="Die Datenbank ist aktuell nicht erreichbar. Bitte später erneut versuchen."), 503
        return render_template("errors/503.html"), 503

    from backend.app.cli import register_cli

    register_cli(app)

    return app
