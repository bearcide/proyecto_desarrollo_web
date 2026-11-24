#!/usr/bin/env bash
# Abre OpenCode, Codex y Antigravity CLI en tres ventanas independientes de GNOME Terminal.
# Uso: bash scripts/abrir_3_agentes.bash [ruta-del-proyecto]
# No instala programas ni modifica el proyecto.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DEFAULT_PROJECT="$HOME/Escritorio/proyecto_CeciyEmilio/proyecto_desarrollo_web"

# Si se guarda dentro de <proyecto>/scripts/, usa automaticamente ese proyecto.
if [[ -d "$SCRIPT_DIR/../backend" && -d "$SCRIPT_DIR/../frontend" ]]; then
  DEFAULT_PROJECT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
fi
PROJECT_DIR="${1:-${IME_PROJECT_DIR:-$DEFAULT_PROJECT}}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  printf 'ERROR: No existe el directorio del proyecto: %s\n' "$PROJECT_DIR" >&2
  exit 1
fi
if ! command -v gnome-terminal >/dev/null 2>&1; then
  printf 'ERROR: GNOME Terminal no esta disponible. Instala gnome-terminal o usa el emulador de terminal de tu sistema.\n' >&2
  exit 1
fi

open_window() {
  local title="$1" tool="$2"
  gnome-terminal --window --title="$title — InscripcionMadeEasy" -- bash -ic '
    cd -- "$1" || exit 1
    export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
    printf "\n=== %s ===\nProyecto: %s\n\n" "$3" "$PWD"
    if command -v "$2" >/dev/null 2>&1; then
      "$2"
      result=$?
      printf "\n%s termino (codigo %s).\n" "$3" "$result"
    else
      printf "No se encontro el comando %s.\n" "$2"
      printf "Comprueba su instalacion y tu PATH.\n"
    fi
    printf "\nLa terminal queda abierta para que puedas revisar mensajes.\n"
    exec bash -i
  ' _ "$PROJECT_DIR" "$tool" "$title"
}

open_window "OpenCode" "opencode"
open_window "Codex" "codex"
open_window "Antigravity" "agy"

printf 'Se solicitaron 3 ventanas de terminal en: %s\n' "$PROJECT_DIR"
