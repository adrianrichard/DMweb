from flask import Blueprint

usuarios_bp = Blueprint("usuarios", __name__)

from app.usuarios import routes  # noqa: E402,F401
