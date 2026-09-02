import sqlite3
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="DentalMatic Web API", version="2.0")

# Ruta exacta a la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), "bd", "consultorioMyM.sqlite3")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    sql_script = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS Odontologos (
        Matricula INTEGER NOT NULL,
        Apellido_odontologo TEXT NOT NULL,
        Nombre_odontologo VARCHAR(50),
        CONSTRAINT Odontologos_PK PRIMARY KEY (Matricula)
    );

    CREATE TABLE IF NOT EXISTS Pacientes (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        NOMBRE VARCHAR(50) NOT NULL,
        APELLIDO VARCHAR(50) NOT NULL,
        domicilio VARCHAR(50),
        telefono INTEGER,
        email VARCHAR(50),
        obrasocial VARCHAR(50),
        nrosocio INTEGER,
        edad INTEGER,
        fechanacimiento DATE
    );

    CREATE TABLE IF NOT EXISTS Odontogramas (
        id_odontograma INTEGER NOT NULL,
        dni_paciente INTEGER NOT NULL,
        fecha DATE NOT NULL,
        odontologo INTEGER NOT NULL DEFAULT '',
        CONSTRAINT ODONTOGRAMAS_PK PRIMARY KEY(id_odontograma),
        CONSTRAINT Odontogramas_Odontologos_FK FOREIGN KEY(odontologo) REFERENCES Odontologos(Matricula),
        CONSTRAINT Odontogramas_Pacientes_FK FOREIGN KEY(dni_paciente) REFERENCES Pacientes(ID)
    );

    CREATE TABLE IF NOT EXISTS Prestaciones (
        id_prestacion INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        tipo_prestacion TEXT NOT NULL,
        fecha DATE NOT NULL,
        paciente INTEGER NOT NULL,
        odontologo INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Turnos (
        Fecha DATE NOT NULL,
        Hora TIME NOT NULL,
        Paciente TEXT NOT NULL,
        Odontologo NUMERIC NOT NULL,
        Prestacion TEXT NOT NULL,
        CONSTRAINT Turnos_PK PRIMARY KEY(Fecha, Hora),
        CONSTRAINT Turnos_Odontologos_FK FOREIGN KEY(Odontologo) REFERENCES Odontologos(Matricula)
    );

    CREATE TABLE IF NOT EXISTS dientes (
        nro INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        nro_diente INTEGER,
        id_odonto INTEGER,
        d TEXT DEFAULT NULL,
        v TEXT DEFAULT NULL,
        m TEXT DEFAULT NULL,
        i REAL DEFAULT NULL,
        o INTEGER DEFAULT NULL,
        extraccion TEXT DEFAULT NULL,
        corona TEXT DEFAULT NULL,
        CONSTRAINT dientes_odontogramas_FK FOREIGN KEY(id_odonto) REFERENCES Odontogramas(id_odontograma)
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario VARCHAR(50),
        pass_usuario VARCHAR(50),
        tipo_usuario VARCHAR(50)
    );
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript(sql_script)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (nombre_usuario, pass_usuario, tipo_usuario)
            VALUES ('admin', 'admin', 'administrador')
        """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# Esquemas Pydantic
# ---------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    mensaje: str
    usuario: str
    tipo_usuario: str

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    domicilio: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    obrasocial: Optional[str] = None
    nrosocio: Optional[str] = None
    edad: Optional[int] = None
    fechanacimiento: Optional[str] = None

class PacienteResponse(PacienteBase):
    id: int

class OdontologoBase(BaseModel):
    matricula: int
    nombre: str
    apellido: str

class OdontologoResponse(OdontologoBase):
    pass

class UsuarioBase(BaseModel):
    nombre_usuario: str
    pass_usuario: str
    tipo_usuario: str

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    tipo_usuario: str

class TurnoBase(BaseModel):
    fecha: str
    hora: str
    paciente: str
    odontologo: int
    prestacion: str

class DienteBase(BaseModel):
    nro_diente: int
    d: Optional[str] = None
    v: Optional[str] = None
    m: Optional[str] = None
    i: Optional[float] = None
    o: Optional[int] = None
    extraccion: Optional[str] = None
    corona: Optional[str] = None

class OdontogramaCreate(BaseModel):
    id_odontograma: int
    dni_paciente: int
    fecha: str
    odontologo: int
    dientes: List[DienteBase] = []

# ---------------------------------------------------------
# API REST - Autenticación
# ---------------------------------------------------------
@app.post("/api/login", response_model=LoginResponse)
def login(datos: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nombre_usuario, pass_usuario, tipo_usuario FROM usuarios WHERE nombre_usuario = ? AND pass_usuario = ?",
        (datos.username, datos.password)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    return {
        "mensaje": "Autenticación exitosa",
        "usuario": user["nombre_usuario"],
        "tipo_usuario": user["tipo_usuario"]
    }

# ---------------------------------------------------------
# API REST - Pacientes
# ---------------------------------------------------------
@app.get("/api/pacientes", response_model=List[PacienteResponse])
def listar_pacientes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID as id, NOMBRE as nombre, APELLIDO as apellido, domicilio, telefono, email, obrasocial, nrosocio, edad, fechanacimiento FROM Pacientes ORDER BY ID DESC")
    filas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in filas]

@app.post("/api/pacientes", status_code=status.HTTP_201_CREATED)
def crear_paciente(paciente: PacienteBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Pacientes (NOMBRE, APELLIDO, domicilio, telefono, email, obrasocial, nrosocio, edad, fechanacimiento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paciente.nombre.upper(),
            paciente.apellido.upper(),
            paciente.domicilio.upper() if paciente.domicilio else "",
            paciente.telefono or "",
            paciente.email or "",
            paciente.obrasocial.upper() if paciente.obrasocial else "",
            paciente.nrosocio or "",
            paciente.edad or 0,
            paciente.fechanacimiento or ""
        ))
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return {"mensaje": "Paciente guardado exitosamente", "id": nuevo_id}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error al registrar paciente: {str(e)}")

@app.delete("/api/pacientes/{paciente_id}")
def eliminar_paciente(paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pacientes WHERE ID = ?", (paciente_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return {"mensaje": "Paciente eliminado exitosamente"}

# ---------------------------------------------------------
# API REST - Odontólogos
# ---------------------------------------------------------
@app.get("/api/odontologos", response_model=List[OdontologoResponse])
def listar_odontologos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Matricula as matricula, Nombre_odontologo as nombre, Apellido_odontologo as apellido FROM Odontologos ORDER BY Matricula ASC")
    filas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in filas]

@app.post("/api/odontologos", status_code=status.HTTP_201_CREATED)
def crear_odontologo(o: OdontologoBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Odontologos (Matricula, Nombre_odontologo, Apellido_odontologo)
            VALUES (?, ?, ?)
        """, (o.matricula, o.nombre.upper(), o.apellido.upper()))
        conn.commit()
        conn.close()
        return {"mensaje": "Odontólogo guardado exitosamente"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="La matrícula ya existe")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error al registrar odontólogo: {str(e)}")

@app.delete("/api/odontologos/{matricula}")
def eliminar_odontologo(matricula: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Odontologos WHERE Matricula = ?", (matricula,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Odontólogo no encontrado")
    return {"mensaje": "Odontólogo eliminado exitosamente"}

# ---------------------------------------------------------
# API REST - Usuarios
# ---------------------------------------------------------
@app.get("/api/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre_usuario, tipo_usuario FROM usuarios ORDER BY id_usuario DESC")
    filas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in filas]

@app.post("/api/usuarios", status_code=status.HTTP_201_CREATED)
def crear_usuario(u: UsuarioBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nombre_usuario, pass_usuario, tipo_usuario)
            VALUES (?, ?, ?)
        """, (u.nombre_usuario, u.pass_usuario, u.tipo_usuario))
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return {"mensaje": "Usuario guardado exitosamente", "id_usuario": nuevo_id}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error al registrar usuario: {str(e)}")

@app.delete("/api/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id_usuario = ?", (usuario_id,))
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    if filas_afectadas == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado exitosamente"}

# ---------------------------------------------------------
# API REST - Turnos
# ---------------------------------------------------------
@app.get("/api/turnos")
def listar_turnos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Fecha, Hora, Paciente, Odontologo, Prestacion FROM Turnos ORDER BY Fecha DESC, Hora DESC")
    filas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in filas]

@app.post("/api/turnos", status_code=status.HTTP_201_CREATED)
def agendar_turno(t: TurnoBase):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Turnos (Fecha, Hora, Paciente, Odontologo, Prestacion)
            VALUES (?, ?, ?, ?, ?)
        """, (t.fecha, t.hora, t.paciente, t.odontologo, t.prestacion))
        conn.commit()
        conn.close()
        return {"mensaje": "Turno agendado exitosamente"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Ya existe un turno en la misma fecha y hora")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error al agendar turno: {str(e)}")

# ---------------------------------------------------------
# API REST - Odontogramas
# ---------------------------------------------------------
@app.get("/api/odontogramas")
def listar_odontogramas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_odontograma, dni_paciente, fecha, odontologo FROM Odontogramas ORDER BY id_odontograma DESC")
    filas = cursor.fetchall()
    conn.close()
    return [dict(row) for row in filas]

@app.post("/api/odontogramas", status_code=status.HTTP_201_CREATED)
def crear_odontograma(data: OdontogramaCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Odontogramas (id_odontograma, dni_paciente, fecha, odontologo)
            VALUES (?, ?, ?, ?)
        """, (data.id_odontograma, data.dni_paciente, data.fecha, data.odontologo))
        
        for d in data.dientes:
            cursor.execute("""
                INSERT INTO dientes (nro_diente, id_odonto, d, v, m, i, o, extraccion, corona)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (d.nro_diente, data.id_odontograma, d.d, d.v, d.m, d.i, d.o, d.extraccion, d.corona))

        conn.commit()
        conn.close()
        return {"mensaje": "Odontograma y dientes guardados exitosamente"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El ID del odontograma ya existe o faltan referencias de paciente/odontólogo.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error al guardar odontograma: {str(e)}")

# ---------------------------------------------------------
# Archivos Estáticos y Vistas HTML
# ---------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def vista_dashboard():
    return FileResponse("static/dashboard.html")