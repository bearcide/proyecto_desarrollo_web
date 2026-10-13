#!/usr/bin/env bash
# =============================================================
# bootstrap.sh
# Configura el entorno local del proyecto de inscripción.
# Uso: bash bootstrap.sh
# =============================================================

set -e  # Detener el script si cualquier comando falla

# Colores para legibilidad
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# -------------------------------------------------------------
# 1. Verificar dependencias del sistema
# -------------------------------------------------------------
log_info "Verificando dependencias del sistema..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 no está instalado. Instálalo y vuelve a intentar."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker no está instalado. Instálalo y vuelve a intentar."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    log_error "Docker Compose (v2) no está disponible. Instálalo y vuelve a intentar."
    exit 1
fi

log_info "Python: $(python3 --version)"
log_info "Docker: $(docker --version)"
log_info "Docker Compose: $(docker compose version | head -n 1)"

# -------------------------------------------------------------
# 2. Crear y activar el entorno virtual
# -------------------------------------------------------------
if [ ! -d "venv" ]; then
    log_info "Creando entorno virtual en venv/..."
    python3 -m venv venv
else
    log_warn "El entorno virtual venv/ ya existe. Se reutiliza."
fi

# shellcheck disable=SC1091
source venv/bin/activate
log_info "Entorno virtual activado."

# -------------------------------------------------------------
# 3. Instalar dependencias de Python
# -------------------------------------------------------------
log_info "Actualizando pip..."
pip install --upgrade pip --quiet

log_info "Instalando dependencias (Django, psycopg2-binary, python-decouple)..."
pip install --quiet django psycopg2-binary python-decouple

# -------------------------------------------------------------
# 4. Crear archivo .env si no existe
# -------------------------------------------------------------
if [ ! -f ".env" ]; then
    log_info "Creando archivo .env con valores de desarrollo..."
    cat > .env <<'EOF'
# Django
DJANGO_SECRET_KEY=django-insecure-cambia-esta-clave-en-produccion
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
POSTGRES_USER=inscripcion_user
POSTGRES_PASSWORD=inscripcion_pass_dev
POSTGRES_DB=inscripcion_db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
EOF
    log_info ".env creado."
else
    log_warn "El archivo .env ya existe. Se respeta el existente."
fi

# -------------------------------------------------------------
# 5. Levantar PostgreSQL con Docker
# -------------------------------------------------------------
log_info "Levantando PostgreSQL con Docker Compose..."
docker compose up -d

log_info "Esperando a que PostgreSQL esté listo..."
for i in {1..30}; do
    if docker exec inscripcion_db pg_isready -U inscripcion_user -d inscripcion_db &> /dev/null; then
        log_info "PostgreSQL está listo."
        break
    fi
    if [ "$i" -eq 30 ]; then
        log_error "PostgreSQL no respondió en 30 intentos. Revisa 'docker compose logs db'."
        exit 1
    fi
    sleep 1
done

# -------------------------------------------------------------
# 6. Aplicar migraciones de Django
# -------------------------------------------------------------
log_info "Aplicando migraciones de Django..."
python manage.py migrate --noinput

# -------------------------------------------------------------
# 7. Resumen final
# -------------------------------------------------------------
echo ""
log_info "============================================"
log_info " Bootstrap completado exitosamente."
log_info "============================================"
echo ""
echo "Próximos pasos:"
echo "  1. Activar el entorno virtual (si abres una terminal nueva):"
echo "       source venv/bin/activate"
echo ""
echo "  2. Crear un superusuario para el admin (solo la primera vez):"
echo "       python manage.py createsuperuser"
echo ""
echo "  3. Levantar el servidor de desarrollo:"
echo "       python manage.py runserver"
echo ""
echo "  4. Abrir en el navegador:"
echo "       http://127.0.0.1:8000/admin/"
echo ""
echo "Para detener PostgreSQL:  docker compose down"
echo "Para borrar los datos:    docker compose down -v"
echo ""