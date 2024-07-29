from functools import wraps
from flask import g, flash, redirect, url_for
from flask_login import current_user

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.rol.NombreRol != role:
                flash('No tienes permiso para acceder a esta página.', 'error')
                return redirect(url_for('home_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
