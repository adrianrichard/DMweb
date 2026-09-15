"""
Rutas de usuarios del sistema.

Reemplaza a modulo_usuario.py:
- ventana() (alta/edición)      -> nuevo() / editar()
- guardar()/actualizar()         -> unificados en las mismas vistas
- eliminar_usuario()             -> eliminar(), con dos resguardos que el
                                     original no tenía: no dejar que te
                                     borres a vos mismo, y no dejar que se
                                     quede el sistema sin ningún administrador
                                     (el original solo protegía al usuario
                                     literal 'admin').

Todas las rutas requieren rol administrador (ver app/decorators.py).
"""

from flask import render_template, redirect, url_for, flash
from flask_login import current_user

from app.usuarios import usuarios_bp
from app.usuarios.forms import UsuarioForm
from app.models import Usuario
from app.decorators import admin_required
from app import db


@usuarios_bp.route("/")
@admin_required
def listado():
    usuarios = Usuario.query.order_by(Usuario.nombre_usuario).all()
    return render_template("usuarios/listado.html", usuarios=usuarios)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo():
    form = UsuarioForm(requiere_clave=True)
    if form.validate_on_submit():
        usuario = Usuario(
            nombre_usuario=form.nombre_usuario.data,
            tipo_usuario=form.tipo_usuario.data,
        )
        usuario.set_password(form.clave.data)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuario guardado correctamente.", "success")
        return redirect(url_for("usuarios.listado"))

    return render_template("usuarios/form.html", form=form, modo="nuevo")


@usuarios_bp.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@admin_required
def editar(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    form = UsuarioForm(
        obj=usuario,
        usuario_id=usuario.id_usuario,
        requiere_clave=False,
    )

    if form.validate_on_submit():
        usuario.nombre_usuario = form.nombre_usuario.data
        usuario.tipo_usuario = form.tipo_usuario.data
        if form.clave.data:  # vacío = no cambiar la contraseña
            usuario.set_password(form.clave.data)
        db.session.commit()
        flash("Usuario actualizado exitosamente.", "success")
        return redirect(url_for("usuarios.listado"))

    return render_template("usuarios/form.html", form=form, modo="editar", usuario=usuario)


@usuarios_bp.route("/<int:id_usuario>/eliminar", methods=["POST"])
@admin_required
def eliminar(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.id_usuario == current_user.id_usuario:
        flash("No podés eliminar tu propio usuario mientras tenés la sesión iniciada.", "warning")
        return redirect(url_for("usuarios.listado"))

    if usuario.tipo_usuario == "administrador":
        otros_admins = Usuario.query.filter(
            Usuario.tipo_usuario == "administrador",
            Usuario.id_usuario != usuario.id_usuario,
        ).count()
        if otros_admins == 0:
            flash("No se puede eliminar: es el único administrador del sistema.", "danger")
            return redirect(url_for("usuarios.listado"))

    db.session.delete(usuario)
    db.session.commit()
    flash(f"Usuario '{usuario.nombre_usuario}' eliminado.", "info")
    return redirect(url_for("usuarios.listado"))
