#!/usr/bin/env bash
# Suite HTTP de integracion del demo contra el backend local.
# Requiere: servidor Django en 127.0.0.1:8000 (settings_demo) y base demo inicializada.
set -e
cd "$(dirname "$0")/../.."
python3 scripts/demo/integration_demo.py --base-url "${IME_DEMO_BASE_URL:-http://127.0.0.1:8000/api/v1}"
