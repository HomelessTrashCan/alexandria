from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from flask import current_app

EMAIL_VERIFY_SALT = "email-verify"
PASSWORD_RESET_SALT = "password-reset"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_token(payload: Any, salt: str) -> str:
    """payload ist meist die E-Mailadresse (str), beim Passwort-Reset zusätzlich
    mit dem aktuellen password_reset_counter kombiniert (list) - siehe User.invalidate_password_reset_tokens."""
    return _serializer().dumps(payload, salt=salt)


def confirm_token(token: str, salt: str) -> Any | None:
    max_age = current_app.config["TOKEN_MAX_AGE_SECONDS"]
    try:
        return _serializer().loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
