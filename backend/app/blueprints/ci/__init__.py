from flask import Blueprint

ci_bp = Blueprint("ci", __name__, url_prefix="/items")

from backend.app.blueprints.ci import routes  # noqa: E402,F401
