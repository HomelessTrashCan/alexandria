from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from backend.app.authorization import permission_required
from backend.app.blueprints.admin import admin_bp
from backend.app.blueprints.admin.forms import ConfigItemTypeForm, CreateUserForm, FieldDefinitionForm
from backend.app.blueprints.auth.tokens import EMAIL_VERIFY_SALT, generate_token
from backend.app.email_utils import send_email
from backend.app.extensions import db
from backend.app.models import ChangeLogEntry, ConfigItemType, FieldDefinition, User
from backend.app.services import ci_types as type_service
from backend.app.services import user_admin as user_admin_service
from domain.permissions import PERMISSIONS
from domain.roles import Role


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
    config_item_type = db.session.get(ConfigItemType, type_id)
    if config_item_type is None:
        # Schon gelöscht (z. B. in einem anderen Fenster) - idempotent, kein 404.
        flash("CI-Typ war bereits gelöscht.", "info")
        return redirect(url_for("admin.list_types"))

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
    field = db.session.get(FieldDefinition, field_id)
    if field is None:
        # Schon gelöscht (z. B. in einem anderen Fenster) - idempotent, kein 404.
        flash("Feld war bereits gelöscht.", "info")
        return redirect(url_for("admin.type_detail", type_id=type_id))
    if field.config_item_type_id != type_id:
        # Keine Race Condition, sondern eine URL-Integritätsprüfung - bleibt ein echter 404.
        abort(404)
    name = field.name
    type_service.delete_field(field)
    flash(f'Feld "{name}" wurde endgültig gelöscht.', "success")
    return redirect(url_for("admin.type_detail", type_id=type_id))


@admin_bp.route("/users")
@permission_required("user.manage")
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template("admin/users_list.html", users=users, roles=Role.ALL)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@permission_required("user.manage")
def new_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = user_admin_service.create_user(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
        )
        token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)
        verify_url = url_for("auth.verify_email", token=token, _external=True)
        send_email(
            to=user.email,
            subject="Alexandria: Konto erstellt - E-Mailadresse bestätigen",
            body=(
                f"Hallo {user.first_name}\n\n"
                "Eine administrierende Person hat ein Konto für dich angelegt. "
                f"Bitte bestätige deine E-Mailadresse, um dich anmelden zu können:\n{verify_url}\n\n"
                "Der Link ist 24 Stunden gültig."
            ),
        )
        flash(f'Konto "{user.username}" wurde angelegt. Eine Bestätigungs-E-Mail wurde versendet.', "success")
        return redirect(url_for("admin.list_users"))
    return render_template("admin/user_form.html", form=form)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@permission_required("user.manage")
def change_user_role(user_id: int):
    target_user = db.session.get(User, user_id)
    if target_user is None:
        flash("Benutzerkonto wurde nicht gefunden.", "danger")
        return redirect(url_for("admin.list_users"))

    new_role = request.form.get("role")
    if new_role not in Role.ALL:
        flash("Ungültige Rolle.", "danger")
        return redirect(url_for("admin.list_users"))

    try:
        user_admin_service.update_role(target_user, new_role, acting_user=current_user)
    except user_admin_service.SelfManagementError as error:
        flash(str(error), "danger")
    else:
        flash(f'Rolle von "{target_user.username}" wurde auf {Role.LABELS[new_role]} geändert.', "success")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@permission_required("user.manage")
def toggle_user_active(user_id: int):
    target_user = db.session.get(User, user_id)
    if target_user is None:
        flash("Benutzerkonto wurde nicht gefunden.", "danger")
        return redirect(url_for("admin.list_users"))

    try:
        user_admin_service.set_active(target_user, active=not target_user.active, acting_user=current_user)
    except user_admin_service.SelfManagementError as error:
        flash(str(error), "danger")
    else:
        flash(f'Konto "{target_user.username}" wurde {"aktiviert" if target_user.active else "deaktiviert"}.', "success")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@permission_required("user.manage")
def delete_user(user_id: int):
    target_user = db.session.get(User, user_id)
    if target_user is None:
        # Schon gelöscht (z. B. in einem anderen Fenster) - idempotent, kein 404.
        flash("Benutzerkonto war bereits gelöscht.", "info")
        return redirect(url_for("admin.list_users"))

    try:
        ok, error = user_admin_service.delete_user(target_user, acting_user=current_user)
    except user_admin_service.SelfManagementError as error:
        flash(str(error), "danger")
        return redirect(url_for("admin.list_users"))

    if ok:
        flash(f'Konto "{target_user.username}" wurde gelöscht.', "success")
    else:
        flash(error, "danger")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/permissions")
@permission_required("audit.read")
def permissions_matrix():
    return render_template("admin/permissions.html", permissions=PERMISSIONS, roles=Role.ALL)


@admin_bp.route("/audit-log")
@permission_required("audit.read")
def audit_log():
    page = request.args.get("page", 1, type=int)
    pagination = ChangeLogEntry.query.order_by(ChangeLogEntry.changed_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("admin/audit_log.html", pagination=pagination)
