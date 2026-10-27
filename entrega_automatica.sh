#!/bin/bash
set -e

echo "=================================================="
echo " 🚀 INICIANDO AUTOMATIZACIÓN DE ENTREGA CLASSROOM"
echo "=================================================="

PROJECT_DIR="$HOME/Escritorio/proyecto_CeciyEmilio/proyecto_desarrollo_web"
cd "$PROJECT_DIR"

# 1. Guardar y subir cambios a GitHub
echo -e "\n[1/3] 📦 Subiendo cambios a la rama feature/migracion-saas-django..."
git add .
git commit -m "feat: agrega Swagger UI drf-spectacular y documentacion DTO POST /alumnos/" || true
git push origin feature/migracion-saas-django

# 2. Verificar o iniciar servidor Django
echo -e "\n[2/3] 🌐 Verificando servidor backend en http://127.0.0.1:8000/docs/..."
if ! curl -s http://127.0.0.1:8000/docs/ > /dev/null; then
    echo "⚙️ Servidor no detectado. Iniciando en segundo plano..."
    source backend/venv/bin/activate
    python backend/manage.py runserver 8000 &
    SERVER_PID=$!
    sleep 3
else
    echo "✅ Servidor activo."
fi

# 3. Instalar herramienta de captura de pantalla e instanciar navegador
echo -e "\n[3/3] 📸 Generando captura de pantalla de Swagger UI..."
source backend/venv/bin/activate
pip install playwright > /dev/null 2>&1
python -m playwright install chromium > /dev/null 2>&1

# Script de Python con Playwright para desplegar el DTO y tomar la foto
python3 - << 'EOF'
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.goto("http://127.0.0.1:8000/docs/", wait_until="networkidle")
    
    # Esperar a que cargue la interfaz de Swagger UI
    page.wait_for_selector(".swagger-ui")
    time.sleep(1)
    
    # Desplegar el bloque de POST /api/v1/alumnos/
    post_block = page.query_selector("div.opblock-post")
    if post_block:
        post_block.click()
        time.sleep(1)
        
    # Guardar imagen en el directorio principal
    output_path = "captura_swagger_classroom.png"
    page.screenshot(path=output_path, full_page=True)
    browser.close()
    print(f"✅ Captura guardada con éxito como '{output_path}'")
EOF

# Apagar el servidor si fue iniciado por el script
if [ -n "$SERVER_PID" ]; then
    echo "🛑 Cerrando servidor en segundo plano..."
    kill $SERVER_PID
fi

echo -e "\n=================================================="
echo "🎉 ¡TODO LISTO PARA ENTREGAR!"
echo "1. Rama 'feature/migracion-saas-django' actualizada en GitHub."
echo "2. Imagen generada: $PROJECT_DIR/captura_swagger_classroom.png"
echo "=================================================="
