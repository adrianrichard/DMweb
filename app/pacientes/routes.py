"""
Rutas de pacientes.

Reemplaza a modulo_paciente.py:
- ventana_paciente() (modo alta)      -> nuevo()
- ventana_paciente() (modo edición)   -> editar()
- guardar() / actualizar()            -> se unifican en las mismas vistas
- calcular_edad()                     -> _calcular_edad() (se recalcula siempre
                                          al guardar, no se confía en un campo
                                          editable como en el original)
- Salir() con confirmación de Tkinter -> el propio botón "Cancelar" del form

El DNI es inmutable una vez creado el paciente (ver forms.py) -> editar()
usa PacienteEditForm, que ni siquiera tiene ese campo.
"""

from datetime import date

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.pacientes import pacientes_bp
from app.pacientes.forms import PacienteForm, PacienteEditForm
from app.models import Paciente
from app import db


def _calcular_edad(fecha_nacimiento):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


def _volcar_datos_comunes(destino, form):
    destino.nombre = form.nombre.data.upper()
    destino.apellido = form.apellido.data.upper()
    destino.domicilio = form.domicilio.data.upper()
    destino.telefono = form.telefono.data
    destino.email = form.email.data
    destino.obrasocial = (form.obrasocial.data or "").upper() or None
    destino.nrosocio = form.nrosocio.data
    destino.fechanacimiento = form.fecha_nacimiento.data
    destino.edad = _calcular_edad(form.fecha_nacimiento.data)


@pacientes_bp.route("/")
@login_required
def listado():
    q = request.args.get("q", "").strip()
    query = Paciente.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Paciente.nombre.ilike(like))
            | (Paciente.apellido.ilike(like))
            | (Paciente.id == q if q.isdigit() else False)
        )
    pacientes = query.order_by(Paciente.apellido, Paciente.nombre).all()
    return render_template("pacientes/listado.html", pacientes=pacientes, q=q)


@pacientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = PacienteForm()
    if form.validate_on_submit():
        paciente = Paciente(id=form.dni.data)
        _volcar_datos_comunes(paciente, form)
        db.session.add(paciente)
        db.session.commit()
        flash("Paciente guardado exitosamente.", "success")
        return redirect(url_for("pacientes.listado"))

    return render_template("pacientes/form.html", form=form, modo="nuevo")


@pacientes_bp.route("/<int:dni>/editar", methods=["GET", "POST"])
@login_required
def editar(dni):
    paciente = Paciente.query.get_or_404(dni)
    form = PacienteEditForm(obj=_a_formdata(paciente))

    if form.validate_on_submit():
        _volcar_datos_comunes(paciente, form)
        db.session.commit()
        flash("Paciente actualizado exitosamente.", "success")
        return redirect(url_for("pacientes.listado"))

    return render_template("pacientes/form.html", form=form, modo="editar", paciente=paciente)


@pacientes_bp.route("/<int:dni>/eliminar", methods=["POST"])
@login_required
def eliminar(dni):
    paciente = Paciente.query.get_or_404(dni)
    db.session.delete(paciente)
    db.session.commit()
    flash(f"Paciente {paciente.apellido}, {paciente.nombre} eliminado.", "info")
    return redirect(url_for("pacientes.listado"))


class _a_formdata:
    """Adaptador chico para precargar el form con los nombres de campo propios
    (fecha_nacimiento en vez de fechanacimiento)."""

    def __init__(self, paciente: Paciente):
        self.nombre = paciente.nombre
        self.apellido = paciente.apellido
        self.fecha_nacimiento = paciente.fechanacimiento
        self.domicilio = paciente.domicilio
        self.telefono = paciente.telefono
        self.email = paciente.email
        self.obrasocial = paciente.obrasocial
        self.nrosocio = paciente.nrosocio
