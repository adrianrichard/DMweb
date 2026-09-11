from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI(title="Sistema Odontológico - DentalMatic")

app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    conn = sqlite3.connect("odontologia.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT UNIQUE NOT NULL,
        pass_usuario TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Odontologos (
        id_odontologo INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        matricula TEXT UNIQUE NOT NULL,
        especialidad TEXT,
        telefono TEXT,
        email TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pacientes (
        id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        dni TEXT UNIQUE NOT NULL,
        fecha_nacimiento TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Turnos (
        id_turno INTEGER PRIMARY KEY AUTOINCREMENT,
        id_paciente INTEGER NOT NULL,
        id_odontologo INTEGER NOT NULL,
        fecha_hora TEXT NOT NULL,
        motivo TEXT,
        estado TEXT DEFAULT 'pendiente',
        FOREIGN KEY (id_paciente) REFERENCES Pacientes(id_paciente),
        FOREIGN KEY (id_odontologo) REFERENCES Odontologos(id_odontologo)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Odontogramas (
        id_odontograma INTEGER PRIMARY KEY AUTOINCREMENT,
        id_paciente INTEGER NOT NULL,
        fecha_creacion TEXT NOT NULL,
        observaciones TEXT,
        FOREIGN KEY (id_paciente) REFERENCES Pacientes(id_paciente)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Prestaciones (
        id_prestacion INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_prestacion TEXT NOT NULL,
        descripcion TEXT,
        costo REAL NOT NULL
    )""")
    
    # Usuario por defecto
    cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (nombre_usuario, pass_usuario, tipo_usuario) VALUES ('admin', 'admin', 'administrador')")
        
    conn.commit()
    conn.close()

init_db()

# --- MODELOS PYDANTIC ---
class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    tipo_usuario: str
    
class LoginRequest(BaseModel):
    nombre_usuario: str
    pass_usuario: str

class UsuarioCreate(BaseModel):
    nombre_usuario: str
    pass_usuario: str
    tipo_usuario: str

class PacienteSchema(BaseModel):
    id_paciente: Optional[int] = None
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

class OdontologoSchema(BaseModel):
    id_odontologo: Optional[int] = None
    nombre: str
    apellido: str
    matricula: str
    especialidad: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class TurnoSchema(BaseModel):
    id_turno: Optional[int] = None
    id_paciente: int
    id_odontologo: int
    fecha_hora: str
    motivo: Optional[str] = None
    estado: Optional[str] = 'pendiente'

class OdontogramaSchema(BaseModel):
    id_odontograma: Optional[int] = None
    id_paciente: int
    fecha_creacion: str
    observaciones: Optional[str] = None

class PrestacionSchema(BaseModel):
    id_prestacion: Optional[int] = None
    nombre_prestacion: str
    descripcion: Optional[str] = None
    costo: float

# --- RUTAS PRINCIPALES ---
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("static/dashboard.html")

@app.post("/api/login")
def login(datos: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id_usuario, nombre_usuario, tipo_usuario FROM usuarios WHERE nombre_usuario = ? AND pass_usuario = ?",
        (datos.nombre_usuario, datos.pass_usuario)
    )
    usuario = cursor.fetchone()
    conn.close()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    return {
        "mensaje": "Inicio de sesión exitoso",
        "usuario": dict(usuario)
    }

# --- API USUARIOS ---
@app.get("/api/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre_usuario, tipo_usuario FROM usuarios ORDER BY id_usuario DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/usuarios", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, pass_usuario, tipo_usuario) VALUES (?, ?, ?)",
            (usuario.nombre_usuario, usuario.pass_usuario, usuario.tipo_usuario)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {**usuario.model_dump(), "id_usuario": user_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

# --- API PACIENTES ---
@app.get("/api/pacientes", response_model=List[PacienteSchema])
def listar_pacientes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pacientes")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/pacientes", response_model=PacienteSchema)
def crear_paciente(paciente: PacienteSchema):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Pacientes (nombre, apellido, dni, fecha_nacimiento, telefono, email, direccion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (paciente.nombre, paciente.apellido, paciente.dni, paciente.fecha_nacimiento, paciente.telefono, paciente.email, paciente.direccion))
        conn.commit()
        p_id = cursor.lastrowid
        conn.close()
        return {**paciente.model_dump(), "id_paciente": p_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="El DNI ya se encuentra registrado")

@app.delete("/api/pacientes/{id_paciente}")
def eliminar_paciente(id_paciente: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pacientes WHERE id_paciente = ?", (id_paciente,))
    conn.commit()
    conn.close()
    return {"mensaje": "Paciente eliminado"}

# --- API ODONTOLOGOS ---
@app.get("/api/odontologos", response_model=List[OdontologoSchema])
def listar_odontologos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Odontologos")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/odontologos", response_model=OdontologoSchema)
def crear_odontologo(odontologo: OdontologoSchema):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Odontologos (nombre, apellido, matricula, especialidad, telefono, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (odontologo.nombre, odontologo.apellido, odontologo.matricula, odontologo.especialidad, odontologo.telefono, odontologo.email))
        conn.commit()
        o_id = cursor.lastrowid
        conn.close()
        return {**odontologo.model_dump(), "id_odontologo": o_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="La matrícula ya se encuentra registrada")

# --- API TURNOS ---
@app.get("/api/turnos", response_model=List[TurnoSchema])
def listar_turnos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Turnos")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/turnos", response_model=TurnoSchema)
def crear_turno(turno: TurnoSchema):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Turnos (id_paciente, id_odontologo, fecha_hora, motivo, estado)
        VALUES (?, ?, ?, ?, ?)
    """, (turno.id_paciente, turno.id_odontologo, turno.fecha_hora, turno.motivo, turno.estado))
    conn.commit()
    t_id = cursor.lastrowid
    conn.close()
    return {**turno.model_dump(), "id_turno": t_id}

# --- API ODONTOGRAMAS ---
@app.get("/api/odontogramas", response_model=List[OdontogramaSchema])
def listar_odontogramas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Odontogramas")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/odontogramas", response_model=OdontogramaSchema)
def crear_odontograma(odontograma: OdontogramaSchema):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Odontogramas (id_paciente, fecha_creacion, observaciones)
        VALUES (?, ?, ?)
    """, (odontograma.id_paciente, odontograma.fecha_creacion, odontograma.observaciones))
    conn.commit()
    od_id = cursor.lastrowid
    conn.close()
    return {**odontograma.model_dump(), "id_odontograma": od_id}

# --- API PRESTACIONES ---
@app.get("/api/prestaciones", response_model=List[PrestacionSchema])
def listar_prestaciones():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Prestaciones")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/prestaciones", response_model=PrestacionSchema)
def crear_prestacion(prestacion: PrestacionSchema):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Prestaciones (nombre_prestacion, descripcion, costo)
        VALUES (?, ?, ?)
    """, (prestacion.nombre_prestacion, prestacion.descripcion, prestacion.costo))
    conn.commit()
    pr_id = cursor.lastrowid
    conn.close()
    return {**prestacion.model_dump(), "id_prestacion": pr_id}

# --- RUTAS DE NAVEGACIÓN ENTRE PÁGINAS ---
@app.get("/usuarios-view")
def read_usuarios_view():
    return FileResponse("static/usuarios.html")

@app.get("/odontologos-view")
def read_odontologos_view():
    return FileResponse("static/odontologos.html")

@app.get("/pacientes-view")
def read_pacientes_view():
    return FileResponse("static/pacientes.html")

@app.get("/turnos-view")
def read_turnos_view():
    return FileResponse("static/turnos.html")

@app.get("/historia-clinica-view")
def read_historia_clinica_view():
    return FileResponse("static/historia_clinica.html")