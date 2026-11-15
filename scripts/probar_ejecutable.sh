#!/usr/bin/env bash
# Prueba de humo del ejecutable ya construido: lo arranca con una carpeta de datos aislada, comprueba que responde (API,
# interfaz, manifiesto, service worker, iconos y a Nova), que crea sus datos en la carpeta del usuario y que NO lee un .env
# ajeno; luego lo detiene. Sirve en Linux, Mac y Windows (Git Bash). Uso: scripts/probar_ejecutable.sh [ruta] [puerto]
set -uo pipefail
cd "$(dirname "$0")/.."
EXE="${1:-}"
[ -z "$EXE" ] && for c in dist-ejecutable/orbit-health dist-ejecutable/orbit-health.exe; do [ -f "$c" ] && EXE="$c" && break; done
[ -f "$EXE" ] || { echo "No encuentro el ejecutable (corre scripts/crear_ejecutable.sh)"; exit 1; }
PUERTO="${2:-3650}"
T="$(mktemp -d)"; trap 'kill "${PID:-0}" 2>/dev/null; rm -rf "$T"' EXIT
export HOME="$T/home" USERPROFILE="$T/home" LOCALAPPDATA="$T/local" XDG_DATA_HOME="$T/data" TMPDIR="$T" TMP="$T" TEMP="$T"
mkdir -p "$HOME" "$LOCALAPPDATA"
printf 'ORBIT_AUTH=1\n' > "$T/.env"                       # justo donde estaría el .env "ajeno" (padre de la carpeta de extracción): no debe leerse
"$EXE" --sin-navegador --puerto "$PUERTO" > "$T/salida.txt" 2>&1 &
PID=$!
fallos=0
ok()  { echo "  ✔ $1"; }
mal() { echo "  ✘ $1"; fallos=$((fallos+1)); }
for _ in $(seq 1 60); do [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PUERTO/api/salud")" = "200" ] && break; sleep 0.5; done
code() { curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PUERTO$1"; }
[ "$(code /api/salud)" = "200" ] && ok "API responde" || mal "API no responde"
[ "$(code /)" = "200" ] && ok "interfaz" || mal "interfaz"
[ "$(code /manifest.webmanifest)" = "200" ] && ok "manifiesto" || mal "manifiesto"
[ "$(code /sw.js)" = "200" ] && ok "service worker" || mal "service worker"
[ "$(code /icono-512.png)" = "200" ] && ok "iconos" || mal "iconos"
curl -s "http://127.0.0.1:$PUERTO/api/tripulantes" | grep -q "Valeria" && ok "tripulación ficticia sembrada" || mal "sin tripulación"
curl -s "http://127.0.0.1:$PUERTO/api/asistente/saludo/T2" | grep -q "Nova" && ok "Nova saluda" || mal "Nova no saluda"
curl -s "http://127.0.0.1:$PUERTO/api/auth/estado" | grep -q '"activa":false' && ok "no leyó un .env ajeno" || mal "leyó un .env ajeno"
ls -R "$T" 2>/dev/null | grep -q "orbit_health.db" && ok "datos creados en la carpeta del usuario" || mal "no creó su base de datos"
echo; [ "$fallos" = 0 ] && echo "Prueba de humo: TODO BIEN" || { echo "Prueba de humo: $fallos fallo(s)"; tail -15 "$T/salida.txt"; }
exit $fallos
