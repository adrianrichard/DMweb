"""
Application factory de DENTALMATIC web.

Patrón "app factory": en vez de crear la instancia de Flask a nivel de módulo,
se crea dentro de una función create_app(). Esto evita imports circulares con
los modelos (app/models.py importa `db` desde acá) y permite tener distintas
configuraciones (desarrollo, testing, producción) o varias instancias en tests.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from config import config

# Extensiones creadas sin app todavía (se "atan" a la app en create_app con init_app).
# Se importan desde app/models.py, app/auth/*, etc. con: from app import db
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Iniciá sesión para acceder a esta página."
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # --- Modelos (necesarios para que Flask-Migrate los detecte) ---
    from app import models  # noqa: F401

    # --- Loader de usuario para Flask-Login ---
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return db.session.get(Usuario, int(user_id))

    # --- Registro de blueprints ---
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.pacientes import pacientes_bp
    app.register_blueprint(pacientes_bp, url_prefix="/pacientes")

    from app.odontologos import odontologos_bp
    app.register_blueprint(odontologos_bp, url_prefix="/odontologos")

    from app.usuarios import usuarios_bp
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")

    # NOTA: turnos todavía no está creado.
    # Cuando armemos ese blueprint, se agrega acá así:
    # from app.turnos import turnos_bp
    # app.register_blueprint(turnos_bp, url_prefix="/turnos")

    # --- Comandos CLI (ej: flask seed-admin) ---
    from app.cli import register_cli_commands
    register_cli_commands(app)

    # --- Ruta raíz: redirige al login (o al dashboard si ya está logueado) ---
    from flask import redirect, url_for, render_template

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def acceso_denegado(e):
        return render_template("errors/403.html"), 403

    return app
