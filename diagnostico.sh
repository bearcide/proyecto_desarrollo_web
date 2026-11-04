#!/usr/bin/env bash

# Colores para salida de consola
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "🔍 DIAGNÓSTICO AUTOMÁTICO DE PROYECTO (FULL-STACK)"
echo "=================================================="
echo ""

ROOT_DIR=$(pwd)

# 1. Estado de Git
echo -e "${YELLOW}📁 [1/4] Verificando estado del repositorio Git...${NC}"
if git rev-parse --is-inside-work-tree &>/dev/null; then
    CHANGES=$(git status --porcelain | wc -l)
    echo "   Archivos modificados o no rastreados: $CHANGES"
    git status -s | head -n 10
else
    echo -e "   ${RED}⚠️ Este directorio no es un repositorio Git.${NC}"
fi
echo ""

# 2. Diagnóstico de Backend (Django)
echo -e "${YELLOW}🐍 [2/4] Escaneando Backend Django...${NC}"
DJANGO_PATH=$(find . -maxdepth 3 -name "manage.py" -not -path "*/node_modules/*" -exec dirname {} \; | head -n 1)

if [ -n "$DJANGO_PATH" ]; then
    echo "   -> Subdirectorio Django hallado en: $DJANGO_PATH"
    cd "$ROOT_DIR/$DJANGO_PATH"
    
    # Activar entorno virtual si existe
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi

    echo "   -> Verificando integridad del código y configuraciones..."
    python3 manage.py check 2>&1
    
    echo "   -> Revisando migraciones de base de datos..."
    PENDING_MIGRATIONS=$(python3 manage.py showmigrations 2>&1 | grep "\[ \]")
    if [ -n "$PENDING_MIGRATIONS" ]; then
        echo -e "   ${RED}⚠️ Hay migraciones pendientes por aplicar:${NC}"
        echo "$PENDING_MIGRATIONS"
    else
        echo -e "   ${GREEN}✓ Base de datos al día / sin migraciones pendientes.${NC}"
    fi
    cd "$ROOT_DIR"
else
    echo -e "   ${RED}⚠️ No se encontró 'manage.py' en el directorio.${NC}"
fi
echo ""

# 3. Diagnóstico de Frontend (React / Vite)
echo -e "${YELLOW}⚛️ [3/4] Escaneando Frontend React...${NC}"
PACKAGE_PATH=$(find . -maxdepth 3 -name "package.json" -not -path "*/node_modules/*" -exec dirname {} \; | head -n 1)

if [ -n "$PACKAGE_PATH" ]; then
    echo "   -> Subdirectorio Frontend hallado en: $PACKAGE_PATH"
    cd "$ROOT_DIR/$PACKAGE_PATH"

    if [ ! -d "node_modules" ]; then
        echo -e "   ${RED}❌ 'node_modules' no existe. Ejecuta 'pnpm install' antes de continuar.${NC}"
    else
        echo "   -> Probando compilación estática para buscar sintaxis/importaciones rotas..."
        if command -v pnpm &> /dev/null; then
            pnpm run build 2>&1
        else
            npm run build 2>&1
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✓ El build del frontend completó sin errores.${NC}"
        else
            echo -e "   ${RED}❌ Se detectaron errores de sintaxis o importación en el Frontend.${NC}"
        fi
    fi
    cd "$ROOT_DIR"
else
    echo -e "   ${RED}⚠️ No se encontró 'package.json'.${NC}"
fi
echo ""

echo "=================================================="
echo "✅ DIAGNÓSTICO FINALIZADO"
echo "=================================================="
