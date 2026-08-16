from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from flask import current_app


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_token(email: str, salt: str) -> str:
    return _serializer().dumps(email, salt=salt)


def confirm_token(token: str, salt: str) -> str | None:
    max_age = current_app.config["TOKEN_MAX_AGE_SECONDS"]
    try:
        return _serializer().loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
