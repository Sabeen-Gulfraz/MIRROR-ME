from functools import wraps
from flask import session, redirect, url_for


def login_required(role=None):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if (role is None and (
                    "user_id" not in session and "tailor_id" not in session and "courier_id" not in session)) or \
                    (role == "Customer" and "user_id" not in session) or \
                    (role == "Tailor" and "tailor_id" not in session) or \
                    (role == "Courier" and "courier_id" not in session):
                return redirect(url_for("home.login"))
            return func(*args, **kwargs)
        return decorated_function
    return wrapper
