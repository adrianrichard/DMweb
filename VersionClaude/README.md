# DENTALMATIC web

Migración de la app de escritorio DENTALMATIC (Tkinter + SQLite) a Flask + PostgreSQL.

## Estructura

```
VersionClaude/
├── config.py
├── run.py
├── requirements.txt
├── .env.example        <- copiar como .env y completar
├── setup.sh             <- instalación automática (ver abajo)
└── app/
    ├── __init__.py       (application factory)
    ├── models.py         (modelos SQLAlchemy)
    ├── cli.py            (comando flask seed-admin)
    ├── auth/             (login/logout)
    ├── pacientes/        (CRUD pacientes)
    ├── odontologos/      (CRUD odontólogos)
    ├── static/uploads/   (para la galería, más adelante)
    └── templates/
```

## Instalación rápida (Linux/macOS)

1. **PostgreSQL** tiene que estar instalado y corriendo (`pg_isready` para comprobar).

2. Crear el usuario y la base, conectado como superusuario:
   ```
   sudo -u postgres psql
   ```
   Dentro de psql:
   ```sql
   CREATE USER dentalmatic WITH PASSWORD 'tu-clave-elegida';
   CREATE DATABASE dentalmatic OWNER dentalmatic;
   \c dentalmatic
   GRANT ALL ON SCHEMA public TO dentalmatic;
   \q
   ```
   (Si la base ya existía de antes: `ALTER DATABASE dentalmatic OWNER TO dentalmatic;` antes del `\c`.)

3. Pararse **dentro** de esta carpeta (`VersionClaude/`, donde está `run.py`) y correr:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```
   La primera vez va a crear un `.env` a partir de `.env.example` y te va a pedir que lo completes
   con la contraseña real (la misma que pusiste en el paso 2) antes de continuar.
   Corré `./setup.sh` de nuevo después de completarlo — instala dependencias, migra la base
   y te pide crear el usuario administrador.

4. Levantar la app:
   ```
   source venv/bin/activate
   flask run
   ```
   Entrar a `http://localhost:5000/`.

## Errores típicos que ya nos pasaron (y su solución)

- **`externally-managed-environment` al hacer pip install** → falta activar el entorno virtual
  (`source venv/bin/activate`). Nunca usar `--break-system-packages`.

- **`ModuleNotFoundError: No module named 'app'`** → estás parado en la carpeta equivocada, o la
  carpeta `app/` no tiene `__init__.py`. Tenés que estar en `VersionClaude/` (donde está `run.py`)
  al correr comandos `flask`.

- **`Failed to find Flask application or factory in module 'app'`** → `FLASK_APP` está mal seteado.
  Tiene que ser `export FLASK_APP=run.py` (no `app`, no `VersionClaude.wsgi`).

- **`fe_sendauth: no password supplied`** → el `.env` no existe, está mal ubicado (tiene que estar
  en `VersionClaude/`, no en la carpeta de arriba), o `DB_PASSWORD` quedó vacío. Recordá: **una
  variable por línea** en el `.env`, nunca todas juntas separadas por espacios.

- **`password authentication failed for user "dentalmatic"`** → la contraseña del `.env` no
  coincide con la de Postgres. Resetearla: `sudo -u postgres psql` → `ALTER USER dentalmatic WITH
  PASSWORD 'lo-que-pusiste-en-el-env';`

- **`permission denied for schema public`** → PostgreSQL 15+ no le da permiso de `CREATE` al owner
  de la base sobre el schema `public` automáticamente. Solución: conectado a la base específica
  (`\c dentalmatic`), correr `GRANT ALL ON SCHEMA public TO dentalmatic;`

- **Comandos que quedan colgados con un `>` en la terminal** → te faltó cerrar una comilla. Ctrl+C
  y reescribir el comando completo con las dos comillas.

- **`Not Found` al entrar a `http://localhost:5000/`** → ya está resuelto en este proyecto (hay una
  ruta `/` que redirige a `/login`), pero si vuelve a pasar, entrar directo a `/login`.

## Decisiones de diseño (por qué está hecho así)

- **DNI de paciente y matrícula de odontólogo son inmutables** una vez creado el registro. Son
  claves primarias referenciadas por Odontogramas/Turnos/Prestaciones — permitir editarlas rompía
  la integridad del historial clínico.
- **Contraseñas hasheadas** (Werkzeug), a diferencia del original que las guardaba en texto plano.
- **No hay auto-creación de la base ni del usuario admin** al arrancar la app (el original creaba
  `admin`/`admin` automáticamente). Ahora es explícito con `flask seed-admin`, por seguridad.

## Pendiente

- Blueprint de **turnos** (calendario) — próximo paso.
- Odontograma, galería, informes, backup: todavía no migrados.
