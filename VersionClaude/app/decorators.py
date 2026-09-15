"""
Decoradores de autorización.

admin_required: además de estar logueado (login_required), exige que
current_user.tipo_usuario == 'administrador'. La gestión de usuarios del
sistema (crear, cambiar roles, eliminar) es más sensible que el CRUD de
pacientes/odontólogos, así que la restringimos — el módulo original de
Tkinter no distinguía esto (cualquier rol que llegara a abrir esa ventana
podía crear usuarios).
"""

from functools import wraps
from flask import abort
from flask_login import current_user, login_required


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.tipo_usuario != "administrador":
            abort(403)
        return f(*args, **kwargs)
    return decorated
