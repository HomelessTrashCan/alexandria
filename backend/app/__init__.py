import json

from flask import Flask

from backend.app.config import Config
from backend.app.extensions import db, jwt, login_manager, mail, migrate
from domain.field_types import FieldType
from domain.permissions import has_permission
from domain.relationship_types import RelationshipType


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

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
        return db.session.get(User, int(user_id))

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
    app.jinja_env.filters["from_json"] = lambda value: json.loads(value) if value else []

    from backend.app.cli import register_cli

    register_cli(app)

    return app
