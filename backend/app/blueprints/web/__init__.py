from flask import Blueprint

web_bp = Blueprint("web", __name__)

from backend.app.blueprints.web import routes  # noqa: E402,F401
