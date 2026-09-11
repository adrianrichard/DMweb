"""
Modelos SQLAlchemy para DENTALMATIC (versión web).

Traducción del schema definido originalmente en conexion.py (crear_bd_login)
usando sqlite3 crudo, a modelos ORM pensados para PostgreSQL con Flask-SQLAlchemy.

Notas de migración SQLite -> PostgreSQL:
- INTEGER PRIMARY KEY AUTOINCREMENT  -> db.Integer, primary_key=True (Postgres usa SERIAL/IDENTITY automáticamente)
- VARCHAR(n) / TEXT                  -> db.String(n) / db.Text
- Los FOREIGN KEY se mantienen igual, pero ahora se expresan también como relationship() para navegar objetos en Python.
- Se agregó un modelo Usuario con password hasheado (en el original la contraseña se guardaba en texto plano).
"""

from datetime import date, time
from flask_login import UserMixin
from app import db  # instancia de Flask-SQLAlchemy creada en app/__init__.py


class Odontologo(db.Model):
    __tablename__ = "odontologos"

    matricula = db.Column(db.Integer, primary_key=True, autoincrement=False)
    apellido = db.Column("apellido_odontologo", db.String(50), nullable=False)
    nombre = db.Column("nombre_odontologo", db.String(50))

    odontogramas = db.relationship("Odontograma", back_populates="odontologo", lazy="dynamic")
    prestaciones = db.relationship("Prestacion", back_populates="odontologo", lazy="dynamic")
    turnos = db.relationship("Turno", back_populates="odontologo", lazy="dynamic")

    def __repr__(self):
        return f"<Odontologo {self.matricula} {self.apellido}, {self.nombre}>"


class Paciente(db.Model):
    __tablename__ = "pacientes"

    # OJO: en modulo_paciente.py el campo 'ID' se completa siempre con el DNI
    # que tipea el usuario (INSERT INTO Pacientes VALUES(dni, ...)), pese a que
    # el schema original lo declaraba AUTOINCREMENT. Acá se refleja el
    # comportamiento real: es una PK numérica sin autoincremento.
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # = DNI
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    domicilio = db.Column(db.String(50))
    telefono = db.Column(db.String(20))  # se pasa a String: permite +54, espacios, 0-adelante, etc.
    email = db.Column(db.String(50))
    obrasocial = db.Column(db.String(50))
    nrosocio = db.Column(db.Integer)
    edad = db.Column(db.Integer)
    fechanacimiento = db.Column(db.Date)

    odontogramas = db.relationship("Odontograma", back_populates="paciente", lazy="dynamic")
    prestaciones = db.relationship("Prestacion", back_populates="paciente", lazy="dynamic")

    def __repr__(self):
        return f"<Paciente {self.id} {self.apellido}, {self.nombre}>"


class Odontograma(db.Model):
    __tablename__ = "odontogramas"

    id_odontograma = db.Column(db.Integer, primary_key=True)
    dni_paciente = db.Column(db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    odontologo_matricula = db.Column(
        "odontologo", db.Integer, db.ForeignKey("odontologos.matricula"), nullable=False
    )

    paciente = db.relationship("Paciente", back_populates="odontogramas")
    odontologo = db.relationship("Odontologo", back_populates="odontogramas")
    dientes = db.relationship("Diente", back_populates="odontograma", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Odontograma {self.id_odontograma} paciente={self.dni_paciente}>"


class Prestacion(db.Model):
    __tablename__ = "prestaciones"

    id_prestacion = db.Column(db.Integer, primary_key=True)
    tipo_prestacion = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    paciente_id = db.Column("paciente", db.Integer, db.ForeignKey("pacientes.id"), nullable=False)
    odontologo_matricula = db.Column(
        "odontologo", db.Integer, db.ForeignKey("odontologos.matricula"), nullable=False
    )

    paciente = db.relationship("Paciente", back_populates="prestaciones")
    odontologo = db.relationship("Odontologo", back_populates="prestaciones")

    def __repr__(self):
        return f"<Prestacion {self.id_prestacion} {self.tipo_prestacion}>"


class Turno(db.Model):
    __tablename__ = "turnos"

    fecha = db.Column(db.Date, primary_key=True)
    hora = db.Column(db.Time, primary_key=True)
    paciente = db.Column(db.String(100), nullable=False)  # texto libre en el original; ver nota abajo
    odontologo_matricula = db.Column(
        "odontologo", db.Integer, db.ForeignKey("odontologos.matricula"), nullable=False
    )
    prestacion = db.Column(db.String(100), nullable=False)

    odontologo = db.relationship("Odontologo", back_populates="turnos")

    def __repr__(self):
        return f"<Turno {self.fecha} {self.hora} {self.paciente}>"


class Diente(db.Model):
    __tablename__ = "dientes"

    nro = db.Column(db.Integer, primary_key=True)
    nro_diente = db.Column(db.Integer)
    id_odonto = db.Column(db.Integer, db.ForeignKey("odontogramas.id_odontograma"))
    d = db.Column(db.String(20))
    v = db.Column(db.String(20))
    m = db.Column(db.String(20))
    i = db.Column(db.Float)
    o = db.Column(db.Integer)
    extraccion = db.Column(db.String(20))
    corona = db.Column(db.String(20))

    odontograma = db.relationship("Odontograma", back_populates="dientes")

    def __repr__(self):
        return f"<Diente {self.nro_diente} odontograma={self.id_odonto}>"


class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    pass_usuario = db.Column(db.String(255), nullable=False)  # hash, no texto plano
    tipo_usuario = db.Column(db.String(50), nullable=False)  # administrador | odontologo | secretario

    def set_password(self, password_plano):
        from werkzeug.security import generate_password_hash
        self.pass_usuario = generate_password_hash(password_plano)

    def check_password(self, password_plano):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pass_usuario, password_plano)

    def get_id(self):
        # UserMixin usa por defecto self.id; nuestra PK se llama id_usuario.
        return str(self.id_usuario)

    def __repr__(self):
        return f"<Usuario {self.nombre_usuario} ({self.tipo_usuario})>"
