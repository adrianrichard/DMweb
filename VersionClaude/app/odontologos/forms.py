"""
Formularios de alta/edición de odontólogos.

Reemplaza a las validaciones de modulo_odontologo.py (validar_alfa, validar_matricula).

DECISIÓN (misma que con el DNI de pacientes): la matrícula es la PK de
Odontologos y está referenciada por FK desde Odontogramas, Prestaciones y
Turnos. Por eso es inmutable una vez creado el odontólogo — no existe un
campo 'matricula' en OdontologoEditForm.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Regexp, Length, NumberRange, ValidationError


class _DatosOdontologoMixin:
    """Campos comunes a alta y edición (todo excepto la matrícula)."""

    apellido = StringField(
        "Apellido",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^[A-Za-zÁÉÍÓÚáéíóú\s]+$", message="Sólo letras."),
            Length(max=50),
        ],
    )
    nombre = StringField(
        "Nombre",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^[A-Za-zÁÉÍÓÚáéíóú\s]+$", message="Sólo letras."),
            Length(max=50),
        ],
    )
    submit = SubmitField("Guardar")


class OdontologoForm(_DatosOdontologoMixin, FlaskForm):
    """Alta de odontólogo nuevo: acá sí se pide y valida la matrícula."""

    matricula = IntegerField(
        "Matrícula",
        validators=[
            DataRequired(message="La matrícula es obligatoria."),
            NumberRange(min=1, message="Sólo números."),
        ],
    )

    def validate_matricula(self, field):
        """Repone verificar_matricula_existente(): no permitir duplicados."""
        from app.models import Odontologo

        if Odontologo.query.get(field.data) is not None:
            raise ValidationError(f"La matrícula {field.data} ya existe.")


class OdontologoEditForm(_DatosOdontologoMixin, FlaskForm):
    """Edición de un odontólogo existente: la matrícula no forma parte de este form."""
    pass
