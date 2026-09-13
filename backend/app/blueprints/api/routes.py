from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from backend.app.blueprints.api import api_bp
from backend.app.blueprints.api.serializers import serialize_change, serialize_item, serialize_type
from backend.app.models import ConfigItem, ConfigItemType, User
from backend.app.services.config_items import search_config_items


@api_bp.route("/auth/login", methods=["POST"])
def login():
    """Token-Login ohne Browser: POST {"username", "password"} -> JWT."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    password = payload.get("password")

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password or ""):
        return jsonify(error="Benutzername oder Kennwort ist falsch."), 401
    if not user.email_verified:
        return jsonify(error="E-Mailadresse ist nicht bestätigt."), 403

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token)


@api_bp.route("/types")
@jwt_required()
def list_types():
    types = ConfigItemType.query.order_by(ConfigItemType.name).all()
    return jsonify([serialize_type(t) for t in types])


@api_bp.route("/items")
@jwt_required()
def list_items():
    query_text = request.args.get("q") or None
    type_id = request.args.get("type_id", type=int)
    status = request.args.get("status") or None

    items = search_config_items(query_text=query_text, type_id=type_id, status=status).all()
    return jsonify([serialize_item(item) for item in items])


@api_bp.route("/items/<int:item_id>")
@jwt_required()
def get_item(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    return jsonify(serialize_item(item, detailed=True))


@api_bp.route("/items/<int:item_id>/history")
@jwt_required()
def get_item_history(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    return jsonify([serialize_change(entry) for entry in item.change_log_entries])
