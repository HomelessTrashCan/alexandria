from functools import wraps

from flask import abort
from flask_login import current_user, login_required

from domain.permissions import has_permission


def permission_required(action: str):
    """Route-Decorator: erfordert Login und die angegebene Berechtigung."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(*args, **kwargs):
            if not has_permission(current_user.role, action):
                abort(403)
            return view(*args, **kwargs)

        return wrapped_view

    return decorator
