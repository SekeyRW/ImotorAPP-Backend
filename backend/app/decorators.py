from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt_identity


def current_user_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_identity = get_jwt_identity()
        g.current_user = user_identity
        return fn(*args, **kwargs)

    return wrapper