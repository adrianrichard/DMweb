#!/bin/bash
# Script de instalación de DENTALMATIC web.
# Correr desde DENTRO de la carpeta VersionClaude/ (donde está este mismo script):
#   chmod +x setup.sh
#   ./setup.sh

set -e  # cortar ante el primer error

# --- 0. Verificar que estamos parados en el lugar correcto ---
if [ ! -f "run.py" ]; then
    echo "❌ No encuentro run.py en esta carpeta."
    echo "   Parate DENTRO de VersionClaude/ (donde está este script) y volvé a correrlo."
    exit 1
fi
echo "✅ Carpeta correcta: $(pwd)"

# --- 1. Entorno virtual ---
if [ ! -d "venv" ]; then
    echo "→ Creando entorno virtual..."
    python3 -m venv venv
else
    echo "✅ Ya existe venv/"
fi

source venv/bin/activate
echo "✅ Entorno virtual activado: $(which python)"

# --- 2. Dependencias ---
echo "→ Instalando dependencias..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo "✅ Dependencias instaladas"

# --- 3. Archivo .env ---
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No existe .env todavía."
    echo "   Se creó un .env de ejemplo a partir de .env.example."
    echo "   ABRILO y completá DB_PASSWORD y SECRET_KEY con valores reales antes de continuar:"
    echo ""
    cp .env.example .env
    echo "   SECRET_KEY sugerido (generado ahora):"
    python -c "import secrets; print('   ' + secrets.token_hex(32))"
    echo ""
    echo "   Editá el archivo .env con: nano .env"
    echo "   Después volvé a correr este script (./setup.sh) para continuar."
    exit 0
else
    echo "✅ Ya existe .env"
fi

# --- 4. Verificar que .env tenga los valores mínimos ---
export $(grep -v '^#' .env | xargs) 2>/dev/null || true
if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" == "reemplazar-con-tu-clave-de-postgres" ]; then
    echo "❌ DB_PASSWORD en .env todavía no está completado con un valor real."
    echo "   Editá el archivo con: nano .env"
    exit 1
fi

# --- 5. Recordatorio de PostgreSQL (esto no se automatiza por seguridad) ---
echo ""
echo "→ Antes de seguir, confirmá que ya existan en PostgreSQL:"
echo "   - el usuario '$DB_USER' con la contraseña que pusiste en .env"
echo "   - la base '$DB_NAME', con owner '$DB_USER'"
echo "   - permisos: GRANT ALL ON SCHEMA public TO $DB_USER;  (conectado a la base $DB_NAME)"
echo ""
read -p "   ¿Ya está todo eso hecho? (s/n) " respuesta
if [ "$respuesta" != "s" ]; then
    echo "   Hacé eso primero (ver README.md, sección PostgreSQL) y volvé a correr ./setup.sh"
    exit 0
fi

# --- 6. Migraciones ---
export FLASK_APP=run.py
if [ ! -d "migrations" ]; then
    echo "→ Inicializando Flask-Migrate..."
    flask db init
fi

echo "→ Generando migración..."
flask db migrate -m "esquema inicial" || echo "   (si dice 'no changes detected', es porque ya estaba migrado — seguimos)"

echo "→ Aplicando migración..."
flask db upgrade
echo "✅ Base de datos migrada"

# --- 7. Usuario administrador ---
echo ""
echo "→ Creando usuario administrador (si ya existe, te va a preguntar si actualizar la clave)"
flask seed-admin

echo ""
echo "🎉 Todo listo. Para levantar la app:"
echo "   source venv/bin/activate   (si no está activado)"
echo "   flask run"
echo "   y entrar a http://localhost:5000/"
