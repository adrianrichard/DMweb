"""
Configuración de DENTALMATIC web.

Las credenciales de la base de datos NUNCA se hardcodean acá: se leen de
variables de entorno. En desarrollo podés definirlas en un archivo .env
(usando python-dotenv) y en producción las setea el servidor/hosting.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Clave usada por Flask para firmar sesiones/cookies. Generar una real con:
    # python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")

    # --- Conexión a PostgreSQL ---
    # Se arma a partir de partes sueltas para no tener que escribir la URL completa,
    # pero también podés setear DATABASE_URL directamente si preferís.
    DB_USER = os.environ.get("DB_USER", "dentalmatic")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "dentalmatic")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Carpeta de subida de archivos (reemplaza a galeria.py sobre disco local)
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB por archivo

    @classmethod
    def init_app(cls, app):
        """Hook para validaciones extra al arrancar la app. No-op por defecto."""
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # A diferencia de Config, acá NO hay valor por defecto inseguro: si falta
    # alguna, se detecta recién al arrancar la app (init_app), no al importar
    # este archivo — así 'flask db init' con FLASK_CONFIG=development no
    # explota por variables de producción que todavía no existen.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    @classmethod
    def init_app(cls, app):
        if not cls.SECRET_KEY:
            raise RuntimeError("Falta la variable de entorno SECRET_KEY en producción.")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("Falta la variable de entorno DATABASE_URL en producción.")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+psycopg2://dentalmatic:@localhost:5432/dentalmatic_test"
    )


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
