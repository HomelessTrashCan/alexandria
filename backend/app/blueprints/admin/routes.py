from flask import abort, flash, redirect, render_template, request, url_for

from backend.app.authorization import permission_required
from backend.app.blueprints.admin import admin_bp
from backend.app.blueprints.admin.forms import ConfigItemTypeForm, FieldDefinitionForm
from backend.app.models import ConfigItemType, FieldDefinition
from backend.app.services import ci_types as type_service


@admin_bp.route("/types")
@permission_required("config_item_type.read")
def list_types():
    types = ConfigItemType.query.order_by(ConfigItemType.name).all()
    return render_template("admin/types_list.html", types=types)


@admin_bp.route("/types/new", methods=["GET", "POST"])
@permission_required("config_item_type.create")
def new_type():
    form = ConfigItemTypeForm()
    if form.validate_on_submit():
        config_item_type = type_service.create_type(form.name.data, form.description.data)
        flash(f'CI-Typ "{config_item_type.name}" wurde angelegt.', "success")
        return redirect(url_for("admin.type_detail", type_id=config_item_type.id))
    return render_template("admin/type_form.html", form=form, is_edit=False)


@admin_bp.route("/types/<int:type_id>")
@permission_required("config_item_type.read")
def type_detail(type_id: int):
    config_item_type = ConfigItemType.query.get_or_404(type_id)
    field_form = FieldDefinitionForm(config_item_type_id=type_id)
    return render_template("admin/type_detail.html", config_item_type=config_item_type, field_form=field_form)


@admin_bp.route("/types/<int:type_id>/edit", methods=["GET", "POST"])
@permission_required("config_item_type.update")
def edit_type(type_id: int):
    config_item_type = ConfigItemType.query.get_or_404(type_id)
    form = ConfigItemTypeForm(original_name=config_item_type.name, obj=config_item_type)
    if form.validate_on_submit():
        type_service.update_type(config_item_type, form.name.data, form.description.data)
        flash(f'CI-Typ "{config_item_type.name}" wurde aktualisiert.', "success")
        return redirect(url_for("admin.type_detail", type_id=config_item_type.id))
    return render_template("admin/type_form.html", form=form, is_edit=True, config_item_type=config_item_type)


@admin_bp.route("/types/<int:type_id>/delete", methods=["POST"])
@permission_required("config_item_type.delete")
def delete_type(type_id: int):
    config_item_type = ConfigItemType.query.get_or_404(type_id)
    name = config_item_type.name
    ok, error = type_service.delete_type(config_item_type)
    if ok:
        flash(f'CI-Typ "{name}" wurde gelöscht.', "success")
        return redirect(url_for("admin.list_types"))
    flash(error, "danger")
    return redirect(url_for("admin.type_detail", type_id=type_id))


@admin_bp.route("/types/<int:type_id>/fields/new", methods=["POST"])
@permission_required("field_definition.create")
def new_field(type_id: int):
    config_item_type = ConfigItemType.query.get_or_404(type_id)
    form = FieldDefinitionForm(config_item_type_id=type_id)
    if form.validate_on_submit():
        type_service.create_field(config_item_type, form.name.data, form.field_type.data, form.required.data, form.options.data)
        flash(f'Feld "{form.name.data}" wurde angelegt.', "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
    return redirect(url_for("admin.type_detail", type_id=type_id))


@admin_bp.route("/types/<int:type_id>/fields/<int:field_id>/edit", methods=["GET", "POST"])
@permission_required("field_definition.update")
def edit_field(type_id: int, field_id: int):
    field = FieldDefinition.query.get_or_404(field_id)
    if field.config_item_type_id != type_id:
        abort(404)

    form = FieldDefinitionForm(config_item_type_id=type_id, original_name=field.name, obj=field)
    if request.method == "GET":
        form.options.data = type_service.options_to_text(field.options)

    if form.validate_on_submit():
        type_service.update_field(field, form.name.data, form.field_type.data, form.required.data, form.options.data)
        flash(f'Feld "{field.name}" wurde aktualisiert.', "success")
        return redirect(url_for("admin.type_detail", type_id=type_id))

    return render_template("admin/field_form.html", form=form, config_item_type=field.config_item_type, field=field)


@admin_bp.route("/types/<int:type_id>/fields/<int:field_id>/archive", methods=["POST"])
@permission_required("field_definition.archive")
def archive_field(type_id: int, field_id: int):
    field = FieldDefinition.query.get_or_404(field_id)
    if field.config_item_type_id != type_id:
        abort(404)
    type_service.set_field_archived(field, archived=not field.archived)
    flash(f'Feld "{field.name}" wurde {"archiviert" if field.archived else "reaktiviert"}.', "success")
    return redirect(url_for("admin.type_detail", type_id=type_id))


@admin_bp.route("/types/<int:type_id>/fields/<int:field_id>/delete", methods=["POST"])
@permission_required("field_definition.delete")
def delete_field(type_id: int, field_id: int):
    field = FieldDefinition.query.get_or_404(field_id)
    if field.config_item_type_id != type_id:
        abort(404)
    name = field.name
    type_service.delete_field(field)
    flash(f'Feld "{name}" wurde endgültig gelöscht.', "success")
    return redirect(url_for("admin.type_detail", type_id=type_id))
