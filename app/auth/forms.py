"""
Formulario de login.

Las expresiones regulares reproducen exactamente las validaciones que tenía
modulo_login.py (validar_nombre / validar_pass), pero ahora se ejecutan del
lado del servidor al enviar el formulario (WTForms), no tecla por tecla como
hacía el validatecommand de Tkinter.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Regexp, Length


class LoginForm(FlaskForm):
    nombre_usuario = StringField(
        "Usuario",
        validators=[
            DataRequired(message="El usuario es obligatorio."),
            Regexp(
                r"^[A-Za-z_]+$",
                message="El nombre de usuario solo puede contener letras y guiones bajos.",
            ),
        ],
    )
    pass_usuario = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria."),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="La contraseña solo puede contener letras, números y guiones bajos.",
            ),
            Length(min=4, message="La contraseña debe tener al menos 4 caracteres."),
        ],
    )
    submit = SubmitField("Ingresar")
