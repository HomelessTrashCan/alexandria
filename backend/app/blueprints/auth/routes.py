from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from backend.app.blueprints.auth import auth_bp
from backend.app.blueprints.auth.forms import (
    LoginForm,
    RegistrationForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
)
from backend.app.blueprints.auth.tokens import confirm_token, generate_token
from backend.app.extensions import db
from backend.app.email_utils import send_email
from backend.app.models import User

EMAIL_VERIFY_SALT = "email-verify"
PASSWORD_RESET_SALT = "password-reset"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)
        verify_url = url_for("auth.verify_email", token=token, _external=True)
        send_email(
            to=user.email,
            subject="CMDB: E-Mailadresse bestätigen",
            body=f"Hallo {user.first_name}\n\nBitte bestätige deine E-Mailadresse:\n{verify_url}\n\nDer Link ist 24 Stunden gültig.",
        )
        flash("Registrierung erfolgreich. Bitte bestätige deine E-Mailadresse über den zugesendeten Link.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify-email/<token>")
def verify_email(token: str):
    email = confirm_token(token, salt=EMAIL_VERIFY_SALT)
    if email is None:
        flash("Der Bestätigungslink ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash("Zu diesem Bestätigungslink wurde kein Konto gefunden.", "danger")
        return redirect(url_for("auth.login"))

    if not user.email_verified:
        user.email_verified = True
        db.session.commit()

    flash("E-Mailadresse bestätigt. Du kannst dich jetzt anmelden.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Benutzername oder Kennwort ist falsch.", "danger")
        elif not user.email_verified:
            flash("Bitte bestätige zuerst deine E-Mailadresse.", "warning")
        elif not user.active:
            flash("Dieses Konto wurde deaktiviert. Bitte wende dich an einen Administrator.", "danger")
        else:
            login_user(user)
            return redirect(url_for("web.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = generate_token(user.email, salt=PASSWORD_RESET_SALT)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_email(
                to=user.email,
                subject="CMDB: Kennwort zurücksetzen",
                body=f"Hallo {user.first_name}\n\nSetze dein Kennwort über diesen Link zurück:\n{reset_url}\n\nDer Link ist 24 Stunden gültig.",
            )
        # Bewusst dieselbe Meldung unabhängig davon, ob die E-Mail existiert
        # (verhindert, dass sich registrierte Adressen erraten lassen).
        flash("Falls die E-Mailadresse registriert ist, wurde ein Link zum Zurücksetzen versendet.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/request_password_reset.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    email = confirm_token(token, salt=PASSWORD_RESET_SALT)
    if email is None:
        flash("Der Link zum Zurücksetzen ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("auth.request_password_reset"))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash("Zu diesem Link wurde kein Konto gefunden.", "danger")
        return redirect(url_for("auth.request_password_reset"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Kennwort wurde geändert. Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
