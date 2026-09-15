"""
Formularios de usuarios del sistema.

Reemplaza a las validaciones de modulo_usuario.py (validar_nombre,
validar_contrasenia). A diferencia de Pacientes/Odontólogos, acá el
'nombre_usuario' NO es la PK real (lo es id_usuario, autoincremental) — el
propio módulo original permitía renombrar un usuario existente — así que un
solo formulario cubre alta y edición, con la contraseña opcional al editar
(dejarla vacía = no cambiarla).
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Regexp, Length, ValidationError


TIPOS_USUARIO = [
    ("administrador", "Administrador"),
    ("odontologo", "Odontólogo"),
    ("secretario", "Secretario"),
]


def _validar_complejidad_password(password):
    """Repone validar_contrasenia(): min 8 caracteres, 1 dígito, 1 mayúscula, 1 minúscula."""
    errores = []
    if len(password) < 8:
        errores.append("Debe contener al menos 8 caracteres.")
    if not any(c.isdigit() for c in password):
        errores.append("Agregar al menos un dígito.")
    if not any(c.isupper() for c in password):
        errores.append("Agregar al menos una mayúscula.")
    if not any(c.islower() for c in password):
        errores.append("Agregar al menos una minúscula.")
    return errores


class UsuarioForm(FlaskForm):
    nombre_usuario = StringField(
        "Nombre de usuario",
        validators=[
            DataRequired(message="Complete este campo."),
            Regexp(
                r"^[a-zA-Z][a-zA-Z_]*$",
                message="Sólo letras o guión bajo. No puede empezar con guión bajo.",
            ),
            Length(max=50),
        ],
    )
    tipo_usuario = SelectField(
        "Tipo de usuario",
        choices=TIPOS_USUARIO,
        validators=[DataRequired(message="Elija un tipo de usuario.")],
    )
    clave = PasswordField("Contraseña", validators=[Optional()])
    submit = SubmitField("Guardar")

    def __init__(self, *args, usuario_id=None, requiere_clave=True, **kwargs):
        """
        usuario_id: id del usuario que se está editando (None si es alta),
                    para no marcar como duplicado el propio nombre.
        requiere_clave: True en alta (la contraseña es obligatoria);
                    False en edición (vacío = no cambiarla).
        """
        super().__init__(*args, **kwargs)
        self.usuario_id = usuario_id
        self.requiere_clave = requiere_clave

    def validate_nombre_usuario(self, field):
        from app.models import Usuario

        existente = Usuario.query.filter_by(nombre_usuario=field.data).first()
        if existente is not None and existente.id_usuario != self.usuario_id:
            raise ValidationError("Ya existe este usuario.")

    def validate_clave(self, field):
        if not field.data:
            if self.requiere_clave:
                raise ValidationError("La contraseña es obligatoria.")
            return  # edición sin cambiar la clave: OK
        errores = _validar_complejidad_password(field.data)
        if errores:
            raise ValidationError(" ".join(errores))
