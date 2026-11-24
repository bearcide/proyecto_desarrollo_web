#!/usr/bin/env bash
# Solo arranca y detiene los dos procesos que crea este script.
set -euo pipefail
checkout=$(realpath "$1")
database=$(realpath "$2")
frontend_port="$3"
api_port="$4"
test_script=$(realpath "$5")
shift 5
python_bin="${PYTHON:-python3}"
if [[ "$(dirname "$database")" != "$checkout/backend" || "$(basename "$database")" != demo_pagos_auditoria_* ]]; then
  echo 'Se requiere una SQLite de auditoría dentro del checkout aislado.' >&2
  exit 1
fi
logs=$(mktemp -d /tmp/ime-auditoria-http.XXXXXX)
printf 'Logs de los procesos temporales: %s\n' "$logs"
PAGOS_DEMO_DATABASE="$database" "$python_bin" "$checkout/backend/manage.py" runserver "127.0.0.1:$api_port" --noreload --settings=config.settings_pagos_demo > "$logs/api.log" 2>&1 &
api_pid=$!
(
  cd "$checkout/frontend"
  export VITE_DEMO_MODE=commercial VITE_API_BASE_URL=/api/v1
  exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$frontend_port" --strictPort
) > "$logs/vite.log" 2>&1 &
vite_pid=$!
trap 'kill "$api_pid" "$vite_pid" 2>/dev/null || true' EXIT
for i in {1..80}; do
  kill -0 "$api_pid"
  kill -0 "$vite_pid"
  if curl -fsS "http://127.0.0.1:$api_port/api/v1/schema/" -o /dev/null 2>/dev/null &&
     curl -fsS "http://127.0.0.1:$frontend_port/login" -o /dev/null 2>/dev/null; then
    IME_API_URL="http://127.0.0.1:$api_port/api/v1" IME_WEB_URL="http://127.0.0.1:$frontend_port" node "$test_script" "$@"
    exit $?
  fi
  sleep 0.25
done
exit 1
