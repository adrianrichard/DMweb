from flask import Blueprint

odontologos_bp = Blueprint("odontologos", __name__)

from app.odontologos import routes  # noqa: E402,F401
