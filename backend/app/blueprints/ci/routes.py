from flask import Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.app.authorization import permission_required
from backend.app.blueprints.ci import ci_bp
from backend.app.blueprints.ci.forms import ConfigItemNameForm, RelationshipForm
from backend.app.extensions import db
from backend.app.models import ConfigItem, ConfigItemRelationship, ConfigItemType
from backend.app.services import config_items as ci_service
from backend.app.services import export as export_service
from domain.ci_status import ConfigItemStatus


def _parse_list_filters() -> dict:
    """Liest die Such-/Filterparameter aus der Query-String - gemeinsam genutzt von list_items und den Export-Routen, damit ein Export immer exakt die aktuell angezeigte/gefilterte Liste widerspiegelt."""
    return {
        "query_text": request.args.get("q") or None,
        "type_id": request.args.get("type_id", type=int),
        "status": request.args.get("status") or None,
        "sort": request.args.get("sort", "name"),
    }


def _active_field_definitions(config_item_type: ConfigItemType):
    return [field for field in config_item_type.fields if not field.archived]


@ci_bp.route("/")
@login_required
def list_items():
    filters = _parse_list_filters()
    items = ci_service.search_config_items(**filters).all()
    types = ConfigItemType.query.order_by(ConfigItemType.name).all()

    return render_template(
        "ci/list.html",
        items=items,
        types=types,
        query_text=filters["query_text"] or "",
        type_id=filters["type_id"],
        status=filters["status"] or "",
        sort=filters["sort"],
        statuses=[(ConfigItemStatus.ACTIVE, ConfigItemStatus.LABELS[ConfigItemStatus.ACTIVE]), (ConfigItemStatus.ARCHIVED, ConfigItemStatus.LABELS[ConfigItemStatus.ARCHIVED])],
    )


@ci_bp.route("/export/csv")
@permission_required("config_item.read")
def export_csv():
    items = ci_service.search_config_items(**_parse_list_filters()).all()
    csv_bytes = export_service.build_csv(items)
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="konfigurationselemente.csv"'},
    )


@ci_bp.route("/export/pdf")
@permission_required("config_item.read")
def export_pdf():
    items = ci_service.search_config_items(**_parse_list_filters()).all()
    pdf_bytes = export_service.build_pdf(items)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="konfigurationselemente.pdf"'},
    )


@ci_bp.route("/new")
@permission_required("config_item.create")
def choose_type():
    types = ConfigItemType.query.order_by(ConfigItemType.name).all()
    return render_template("ci/select_type.html", types=types)


@ci_bp.route("/new/<int:type_id>", methods=["GET", "POST"])
@permission_required("config_item.create")
def new_item(type_id: int):
    config_item_type = ConfigItemType.query.get_or_404(type_id)
    field_definitions = _active_field_definitions(config_item_type)

    form = ConfigItemNameForm()
    field_errors: dict[int, str] = {}

    if form.validate_on_submit():
        _values, field_errors = ci_service.validate_field_values(field_definitions, request.form)
        if not field_errors:
            item = ci_service.create_config_item(config_item_type, form.name.data, field_definitions, request.form, current_user)
            flash(f'Konfigurationselement "{item.name}" wurde angelegt.', "success")
            return redirect(url_for("ci.detail", item_id=item.id))

    return render_template(
        "ci/form.html",
        form=form,
        config_item_type=config_item_type,
        field_definitions=field_definitions,
        field_values={},
        field_errors=field_errors,
        is_edit=False,
    )


@ci_bp.route("/<int:item_id>")
@permission_required("config_item.read")
def detail(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    relationship_form = RelationshipForm()
    relationship_form.target_id.choices = [
        (ci.id, f"{ci.name} ({ci.config_item_type.name})") for ci in ConfigItem.query.filter(ConfigItem.id != item.id).order_by(ConfigItem.name).all()
    ]
    return render_template("ci/detail.html", item=item, relationship_form=relationship_form)


@ci_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@permission_required("config_item.update")
def edit_item(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    field_definitions = _active_field_definitions(item.config_item_type)
    current_values = {fv.field_definition_id: fv.value for fv in item.field_values}

    form = ConfigItemNameForm(name=item.name)
    field_errors: dict[int, str] = {}

    if form.validate_on_submit():
        _values, field_errors = ci_service.validate_field_values(field_definitions, request.form)
        if not field_errors:
            submitted_version = request.form.get("version", type=int)
            try:
                ci_service.update_config_item(item, form.name.data, field_definitions, request.form, current_user, expected_version=submitted_version)
            except ci_service.ConcurrentModificationError as error:
                flash(str(error), "danger")
                return redirect(url_for("ci.edit_item", item_id=item.id))
            flash(f'Konfigurationselement "{item.name}" wurde aktualisiert.', "success")
            return redirect(url_for("ci.detail", item_id=item.id))
        current_values = {
            field.id: (request.form.get(f"field_{field.id}") or "") for field in field_definitions
        }

    return render_template(
        "ci/form.html",
        form=form,
        config_item_type=item.config_item_type,
        field_definitions=field_definitions,
        field_values=current_values,
        field_errors=field_errors,
        is_edit=True,
        version=item.version,
        item=item,
    )


@ci_bp.route("/<int:item_id>/archive", methods=["POST"])
@permission_required("config_item.archive")
def archive_item(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    ci_service.set_archived(item, archived=True, user=current_user)
    flash(f'"{item.name}" wurde archiviert.', "success")
    return redirect(url_for("ci.detail", item_id=item.id))


@ci_bp.route("/<int:item_id>/unarchive", methods=["POST"])
@permission_required("config_item.delete")  # Reaktivieren ist in der RBAC-Matrix nicht separat geregelt; an "loeschen" (Admin) angelehnt.
def unarchive_item(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    ci_service.set_archived(item, archived=False, user=current_user)
    flash(f'"{item.name}" wurde reaktiviert.', "success")
    return redirect(url_for("ci.detail", item_id=item.id))


@ci_bp.route("/<int:item_id>/delete", methods=["POST"])
@permission_required("config_item.delete")
def delete_item(item_id: int):
    item = db.session.get(ConfigItem, item_id)
    if item is None:
        # Bereits geloescht (z. B. zeitgleich in einem anderen Fenster) - idempotent behandeln, kein 404 (siehe docs/toDo.md).
        flash("Konfigurationselement war bereits gelöscht.", "info")
        return redirect(url_for("ci.list_items"))

    name = item.name
    ci_service.delete_config_item(item)
    flash(f'"{name}" wurde endgültig gelöscht.', "success")
    return redirect(url_for("ci.list_items"))


@ci_bp.route("/<int:item_id>/relationships", methods=["POST"])
@permission_required("config_item.link")
def add_relationship(item_id: int):
    item = ConfigItem.query.get_or_404(item_id)
    form = RelationshipForm()
    form.target_id.choices = [
        (ci.id, ci.name) for ci in ConfigItem.query.filter(ConfigItem.id != item.id).all()
    ]

    if form.validate_on_submit():
        target = ConfigItem.query.get_or_404(form.target_id.data)
        try:
            ci_service.add_relationship(item, target, form.relationship_type.data, current_user)
        except (ci_service.DuplicateRelationshipError, ci_service.SelfReferenceError) as error:
            flash(str(error), "warning")
        else:
            flash(f'Beziehung zu "{target.name}" wurde angelegt.', "success")
    else:
        flash("Beziehung konnte nicht angelegt werden.", "danger")

    return redirect(url_for("ci.detail", item_id=item.id))


@ci_bp.route("/<int:item_id>/relationships/<int:relationship_id>/delete", methods=["POST"])
@permission_required("config_item.unlink")
def delete_relationship(item_id: int, relationship_id: int):
    relationship = db.session.get(ConfigItemRelationship, relationship_id)
    if relationship is None or relationship.source_id != item_id:
        # Bereits entfernt - z. B. weil ein anderes Browserfenster dieselbe
        # Aktion schon ausgefuehrt hat. Loeschen wird idempotent behandelt:
        # der gewuenschte Endzustand (Beziehung existiert nicht mehr) ist
        # bereits erreicht, das ist kein Fehler und kein 404.
        flash("Beziehung war bereits entfernt.", "info")
        return redirect(url_for("ci.detail", item_id=item_id))

    ci_service.remove_relationship(relationship, current_user)
    flash("Beziehung wurde entfernt.", "success")
    return redirect(url_for("ci.detail", item_id=item_id))
