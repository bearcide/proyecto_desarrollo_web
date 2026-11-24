#!/usr/bin/env bash
# Ejecutar tras terminar auditoria.py. La navegación muta solo una copia nueva.
set -euo pipefail
area=$(cd "$(dirname "$0")" && pwd)
checkout=$(realpath "$1")
evidence=$(realpath "$2")
browser_artifacts="$3"
db="$checkout/backend/demo_pagos_auditoria_$(basename "$evidence").sqlite3"
copy="$checkout/backend/demo_pagos_auditoria_browser_$(date +%s%N).sqlite3"
python_bin="${PYTHON:-python3}"
"$python_bin" "$area/aislamiento.py" --checkout "$checkout" --evidencia "$evidence"
"$python_bin" "$area/copiar-base-auditoria.py" "$db" "$copy"
bash "$area/correr-navegador.sh" "$checkout" "$copy" 15174 18084 "$area/navegador.cjs" "$evidence" "$browser_artifacts"
