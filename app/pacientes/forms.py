"""
Formularios de alta/edición de pacientes.

Reemplaza a completar_campos() + validar_datos() de modulo_paciente.py.
Diferencia deliberada: la fecha de nacimiento se pide con un <input type="date">
(DateField) en vez del formato de texto libre "DD-MM-AAAA" que validaba a mano
el original con una regex — el navegador ya garantiza un formato válido.

DECISIÓN: el DNI (PK de Pacientes, y referenciado por FK desde Odontogramas)
sólo se puede cargar al crear el paciente. Una vez creado, es inmutable — por
eso NO existe un campo 'dni' en PacienteEditForm. Si alguien se equivocó al
tipear el DNI, la vía correcta es eliminar el paciente y cargarlo de nuevo
(o, si ya tiene historial clínico, resolverlo con una migración de datos
puntual, no desde esta pantalla).
"""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SubmitField
from wtforms.validators import (
    DataRequired,
    Optional,
    Regexp,
    Length,
    Email,
    NumberRange,
    ValidationError,
)


class _DatosPacienteMixin:
    """Campos comunes a alta y edición (todo excepto el DNI)."""

    nombre = StringField(
        "Nombre/s",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", message="Sólo letras."),
            Length(max=50),
        ],
    )
    apellido = StringField(
        "Apellido/s",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", message="Sólo letras."),
            Length(max=50),
        ],
    )
    fecha_nacimiento = DateField(
        "Fecha de nacimiento",
        validators=[DataRequired(message="Complete este campo.")],
    )
    domicilio = StringField(
        "Domicilio",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s]+$", message="Sólo letras y/o números."),
            Length(max=50),
        ],
    )
    telefono = StringField(
        "Teléfono",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(r"^\d+$", message="Sólo números, hasta 11 dígitos."),
            Length(max=11),
        ],
    )
    email = StringField(
        "Email",
        validators=[Optional(), Email(message="Formato inválido.")],
    )
    obrasocial = StringField("Obra Social", validators=[Optional(), Length(max=50)])
    nrosocio = IntegerField("Nro de socio", validators=[Optional()])
    submit = SubmitField("Guardar")

    def validate_fecha_nacimiento(self, field):
        """Repone las validaciones de rango que hacía calcular_edad()."""
        if field.data > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser futura.")
        edad_aproximada = date.today().year - field.data.year
        if edad_aproximada > 120:
            raise ValidationError("Edad improbable, verifique la fecha.")


class PacienteForm(_DatosPacienteMixin, FlaskForm):
    """Alta de paciente nuevo: acá sí se pide y valida el DNI."""

    dni = IntegerField(
        "D.N.I.",
        validators=[
            DataRequired(message="El D.N.I. es obligatorio."),
            NumberRange(min=1, max=99_999_999, message="Sólo números, hasta 8 dígitos."),
        ],
    )

    def validate_dni(self, field):
        """Repone dni_existe(): no permitir crear un paciente con un DNI ya cargado."""
        from app.models import Paciente

        if Paciente.query.get(field.data) is not None:
            raise ValidationError(
                f"Ya existe un paciente registrado con el DNI {field.data}. "
                "Verifique los datos o utilice la opción 'Editar'."
            )


class PacienteEditForm(_DatosPacienteMixin, FlaskForm):
    """Edición de un paciente existente: el DNI no forma parte de este form."""
    pass
