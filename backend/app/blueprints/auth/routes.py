from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from backend.app.blueprints.auth import auth_bp
from backend.app.blueprints.auth.forms import (
    AccountForm,
    AdminAccountForm,
    ChangeOwnPasswordForm,
    LoginForm,
    RegistrationForm,
    RequestPasswordResetForm,
    ResetPasswordForm,
)
from backend.app.blueprints.auth.tokens import EMAIL_VERIFY_SALT, PASSWORD_RESET_SALT, confirm_token, generate_token
from backend.app.extensions import db
from backend.app.email_utils import send_email
from backend.app.models import User
from domain.roles import Role


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
            subject="Alexandria: E-Mailadresse bestätigen",
            body=f"Hallo {user.first_name}\n\nBitte bestätige deine E-Mailadresse:\n{verify_url}\n\nDer Link ist 24 Stunden gültig.",
        )
        flash("Registrierung erfolgreich. Bitte bestätige deine E-Mailadresse über den zugesendeten Link.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify-email/<token>", methods=["GET", "POST"])
def verify_email(token: str):
    """GET zeigt nur eine Bestätigungsseite, die eigentliche Verifizierung
    passiert erst beim POST (Button-Klick).

    Wichtig: ein GET darf laut HTTP keine Zustandsänderung auslösen ("sichere
    Methode"). Viele E-Mail-Sicherheitsscanner (Microsoft Defender, Proofpoint
    u. Ä.) rufen jeden Link in eingehenden Mails automatisch per GET auf, um
    ihn zu prüfen - würde GET hier direkt verifizieren, wäre das Konto schon
    bestätigt, bevor der Mensch die Mail überhaupt öffnet.
    """
    email = confirm_token(token, salt=EMAIL_VERIFY_SALT)
    if email is None:
        flash("Der Bestätigungslink ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash("Zu diesem Bestätigungslink wurde kein Konto gefunden.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if not user.email_verified:
            user.email_verified = True
            db.session.commit()
        flash("E-Mailadresse bestätigt. Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash("E-Mailadresse ist bereits bestätigt. Du kannst dich anmelden.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/verify_email.html")


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
            # Entwertet alle zuvor angeforderten, noch nicht eingelösten
            # Reset-Links für dieses Konto - nur der zuletzt versendete Link
            # soll gültig sein, nicht "first come, first served".
            user.invalidate_password_reset_tokens()
            db.session.commit()
            token = generate_token([user.email, user.password_reset_counter], salt=PASSWORD_RESET_SALT)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_email(
                to=user.email,
                subject="Alexandria: Kennwort zurücksetzen",
                body=f"Hallo {user.first_name}\n\nSetze dein Kennwort über diesen Link zurück:\n{reset_url}\n\nDer Link ist 24 Stunden gültig.",
            )
        # Bewusst dieselbe Meldung unabhängig davon, ob die E-Mail existiert
        # (verhindert, dass sich registrierte Adressen erraten lassen).
        flash("Falls die E-Mailadresse registriert ist, wurde ein Link zum Zurücksetzen versendet.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/request_password_reset.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    payload = confirm_token(token, salt=PASSWORD_RESET_SALT)
    if not isinstance(payload, list) or len(payload) != 2:
        flash("Der Link zum Zurücksetzen ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("auth.request_password_reset"))
    email, counter = payload

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash("Zu diesem Link wurde kein Konto gefunden.", "danger")
        return redirect(url_for("auth.request_password_reset"))

    if user.password_reset_counter != counter:
        # Der Link wurde bereits verwendet (oder das Passwort wurde
        # zwischenzeitlich anders geändert) - ein einmal benutzter
        # Reset-Link darf kein zweites Mal funktionieren.
        flash("Der Link zum Zurücksetzen wurde bereits verwendet oder ist abgelaufen.", "danger")
        return redirect(url_for("auth.request_password_reset"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Kennwort wurde geändert. Du kannst dich jetzt anmelden.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    is_admin = current_user.role == Role.ADMIN
    form = AdminAccountForm(current_user_id=current_user.id, obj=current_user) if is_admin else AccountForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        if is_admin and form.email.data != current_user.email:
            current_user.email = form.email.data
            # Eine neue, noch unbestätigte Adresse darf nicht als verifiziert
            # gelten - dieselbe Regel wie bei der Registrierung.
            current_user.email_verified = False
            db.session.commit()

            token = generate_token(current_user.email, salt=EMAIL_VERIFY_SALT)
            verify_url = url_for("auth.verify_email", token=token, _external=True)
            send_email(
                to=current_user.email,
                subject="Alexandria: E-Mailadresse bestätigen",
                body=f"Hallo {current_user.first_name}\n\nBitte bestätige deine neue E-Mailadresse:\n{verify_url}\n\nDer Link ist 24 Stunden gültig.",
            )
            flash("Profil aktualisiert. Bitte bestätige deine neue E-Mailadresse über den zugesendeten Link.", "warning")
        else:
            db.session.commit()
            flash("Profil aktualisiert.", "success")
        return redirect(url_for("auth.account"))

    return render_template("auth/account.html", form=form, password_form=ChangeOwnPasswordForm(), is_admin=is_admin)


@auth_bp.route("/account/password", methods=["POST"])
@login_required
def change_own_password():
    form = ChangeOwnPasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Aktuelles Kennwort ist falsch.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Kennwort wurde geändert.", "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
    return redirect(url_for("auth.account"))
