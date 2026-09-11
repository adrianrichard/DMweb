from flask import Blueprint

pacientes_bp = Blueprint("pacientes", __name__)

from app.pacientes import routes  # noqa: E402,F401
