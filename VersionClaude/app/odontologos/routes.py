"""
Rutas de odontólogos.

Reemplaza a modulo_odontologo.py:
- ventana() (modo alta)                -> nuevo()
- ventana() (modo edición)              -> editar()
- guardar_odontologo()/actualizar_odontologo() -> se unifican en las mismas vistas
- eliminar_odontologo() con askquestion  -> eliminar() con confirm() en el template
- Salir() con confirmación de Tkinter    -> botón "Cancelar" del form

La matrícula es inmutable una vez creado el odontólogo (ver forms.py).
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.odontologos import odontologos_bp
from app.odontologos.forms import OdontologoForm, OdontologoEditForm
from app.models import Odontologo
from app import db


@odontologos_bp.route("/")
@login_required
def listado():
    q = request.args.get("q", "").strip()
    query = Odontologo.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Odontologo.nombre.ilike(like))
            | (Odontologo.apellido.ilike(like))
            | (Odontologo.matricula == q if q.isdigit() else False)
        )
    odontologos = query.order_by(Odontologo.apellido, Odontologo.nombre).all()
    return render_template("odontologos/listado.html", odontologos=odontologos, q=q)


@odontologos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = OdontologoForm()
    if form.validate_on_submit():
        odontologo = Odontologo(
            matricula=form.matricula.data,
            apellido=form.apellido.data.upper(),
            nombre=form.nombre.data.upper(),
        )
        db.session.add(odontologo)
        db.session.commit()
        flash("Odontólogo guardado exitosamente.", "success")
        return redirect(url_for("odontologos.listado"))

    return render_template("odontologos/form.html", form=form, modo="nuevo")


@odontologos_bp.route("/<int:matricula>/editar", methods=["GET", "POST"])
@login_required
def editar(matricula):
    odontologo = Odontologo.query.get_or_404(matricula)
    form = OdontologoEditForm(obj=odontologo)

    if form.validate_on_submit():
        odontologo.apellido = form.apellido.data.upper()
        odontologo.nombre = form.nombre.data.upper()
        db.session.commit()
        flash("Odontólogo actualizado exitosamente.", "success")
        return redirect(url_for("odontologos.listado"))

    return render_template("odontologos/form.html", form=form, modo="editar", odontologo=odontologo)


@odontologos_bp.route("/<int:matricula>/eliminar", methods=["POST"])
@login_required
def eliminar(matricula):
    odontologo = Odontologo.query.get_or_404(matricula)
    try:
        db.session.delete(odontologo)
        db.session.commit()
        flash(f"Odontólogo {odontologo.apellido}, {odontologo.nombre} eliminado.", "info")
    except IntegrityError:
        db.session.rollback()
        flash(
            "No se puede eliminar: el odontólogo tiene odontogramas, "
            "turnos o prestaciones asociadas.",
            "danger",
        )
    return redirect(url_for("odontologos.listado"))
