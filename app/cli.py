"""
Comandos CLI de DENTALMATIC.

Reemplaza al fragmento de crear_bd_login() que insertaba un usuario
'admin'/'admin' automáticamente al detectar que la base no existía. Ese
comportamiento es riesgoso en una app web (usuario y clave conocidos,
expuestos a internet), así que ahora es un paso manual y explícito:

    flask seed-admin

Pide usuario y contraseña por consola (o los toma de variables de entorno /
opciones), y crea el registro con la contraseña ya hasheada.
"""

import click
from flask.cli import with_appcontext

from app import db
from app.models import Usuario


@click.command("seed-admin")
@click.option("--username", prompt="Usuario administrador", default="admin", show_default=True)
@click.option(
    "--password",
    prompt="Contraseña",
    hide_input=True,
    confirmation_prompt=True,
    help="Si no se pasa, se pide de forma interactiva y oculta.",
)
@with_appcontext
def seed_admin(username, password):
    """Crea (o actualiza la contraseña de) el usuario administrador inicial."""

    existente = Usuario.query.filter_by(nombre_usuario=username).first()

    if existente:
        if not click.confirm(
            f"El usuario '{username}' ya existe. ¿Actualizar su contraseña?"
        ):
            click.echo("Cancelado.")
            return
        existente.set_password(password)
        existente.tipo_usuario = "administrador"
        db.session.commit()
        click.echo(f"Contraseña de '{username}' actualizada.")
        return

    nuevo_admin = Usuario(nombre_usuario=username, tipo_usuario="administrador")
    nuevo_admin.set_password(password)
    db.session.add(nuevo_admin)
    db.session.commit()
    click.echo(f"Usuario administrador '{username}' creado correctamente.")


def register_cli_commands(app):
    app.cli.add_command(seed_admin)
