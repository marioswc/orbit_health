#!/usr/bin/env bash
# Prueba REAL del acceso directo con icono en el sistema donde corre (Linux, Mac o Windows con Git Bash): pide al ejecutable que lo
# instale, comprueba que existe y es válido, lo quita y comprueba que se fue. Uso: scripts/probar_acceso.sh [ruta-al-ejecutable]
set -uo pipefail
cd "$(dirname "$0")/.."
EXE="${1:-}"; [ -z "$EXE" ] && for c in dist-ejecutable/orbit-health.exe dist-ejecutable/orbit-health; do [ -f "$c" ] && EXE="$c" && break; done
[ -f "$EXE" ] || { echo "No encuentro el ejecutable"; exit 1; }
fallos=0; ok() { echo "  ✔ $1"; }; mal() { echo "  ✘ $1"; fallos=$((fallos+1)); }
esperar() { for _ in $(seq 1 40); do eval "$1" && return 0; sleep 0.5; done; return 1; }   # un .exe sin consola no hace esperar a bash
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) MENU="$(cygpath -u "$APPDATA")/Microsoft/Windows/Start Menu/Programs/ORBIT Health.lnk"
    "$EXE" --instalar-acceso >/dev/null 2>&1 & esperar '[ -f "$MENU" ]' && ok "acceso en el menú Inicio" || mal "no se creó el acceso en el menú Inicio"
    [ -s "$MENU" ] && ok "el .lnk no está vacío" || mal "el .lnk está vacío"
    "$EXE" --quitar-acceso >/dev/null 2>&1 & esperar '[ ! -f "$MENU" ]' && ok "se quitó" || mal "no se quitó";;
  Darwin) APP="$HOME/Applications/ORBIT Health.app"
    "$EXE" --instalar-acceso >/dev/null 2>&1; [ -x "$APP/Contents/MacOS/orbit-health" ] && ok "ORBIT Health.app creada" || mal "no se creó la app"
    plutil -lint "$APP/Contents/Info.plist" >/dev/null 2>&1 && ok "Info.plist válido" || mal "Info.plist inválido"
    [ -s "$APP/Contents/Resources/orbit.icns" ] && ok "icono incluido" || mal "falta el icono"
    "$EXE" --quitar-acceso >/dev/null 2>&1; [ ! -d "$APP" ] && ok "se quitó" || mal "no se quitó";;
  *) D="${XDG_DATA_HOME:-$HOME/.local/share}"
    "$EXE" --instalar-acceso >/dev/null 2>&1; [ -f "$D/applications/orbit-health.desktop" ] && ok "acceso en el menú de aplicaciones" || mal "no se creó el acceso"
    [ -s "$D/orbit-health/icono.png" ] && ok "icono incluido" || mal "falta el icono"
    if command -v desktop-file-validate >/dev/null; then desktop-file-validate "$D/applications/orbit-health.desktop" && ok "cumple el estándar freedesktop" || mal "no cumple el estándar"; fi
    "$EXE" --quitar-acceso >/dev/null 2>&1; [ ! -f "$D/applications/orbit-health.desktop" ] && ok "se quitó" || mal "no se quitó";;
esac
[ "$fallos" = 0 ] && echo "Acceso directo: TODO BIEN" || echo "Acceso directo: $fallos fallo(s)"; exit $fallos
