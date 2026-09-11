"""
Rutas de autenticación.

Reemplaza a modulo_login.py:
- Login.verificar()  -> vista login() de acá abajo
- messagebox de éxito/error -> flash()
- MasterPanel(usuario[2]) -> redirect a un dashboard según el rol

Diferencia importante con el original: ya NO se crea la base de datos ni el
usuario admin por defecto desde el login (eso ahora lo maneja Flask-Migrate +
un comando de seed aparte). Si las credenciales no coinciden, simplemente se
informa error; no se asume que la app está recién instalada.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import LoginForm
from app.models import Usuario


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está logueado, no tiene sentido mostrarle el form de nuevo
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login_redirect"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(nombre_usuario=form.nombre_usuario.data).first()

        if usuario is not None and usuario.check_password(form.pass_usuario.data):
            # tipo_usuario puede ser: administrador | odontologo | secretario
            login_user(usuario)
            flash("Ingreso autorizado.", "success")
            return redirect(url_for("auth.post_login_redirect"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/post-login")
@login_required
def post_login_redirect():
    """
    Punto único de redirección post-login. Reemplaza a los tres 'if' de
    modulo_login.py (administrador / odontologo / secretario) que abrían
    el mismo MasterPanel con distinto rol.

    Por ahora los tres roles comparten el mismo dashboard; si necesitás
    pantallas de inicio distintas por rol, se puede ramificar acá.
    """
    return render_template("auth/dashboard.html", usuario=current_user)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
