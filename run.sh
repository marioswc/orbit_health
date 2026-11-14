#!/usr/bin/env bash
# Arranque local de ORBIT Health. Requiere haber preparado dependencias (con red) una vez.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }
PUERTO="${ORBIT_PUERTO:-3000}"
HOST="${ORBIT_HOST:-127.0.0.1}"

# Sin autenticación por tripulante, exponer el servicio en la red de la cabina deja los datos de salud
# visibles para cualquier dispositivo conectado. Solo se permite con confirmación explícita.
case "$HOST" in
  127.0.0.1|localhost|::1) ;;
  *) [ "${ORBIT_PERMITIR_RED:-0}" = "1" ] || {
       echo "ORBIT_HOST=$HOST expone los datos en la red y aún no hay autenticación por tripulante."
       echo "Si es una red aislada y confiable, confirma con ORBIT_PERMITIR_RED=1."; exit 1; } ;;
esac

[ -d frontend/dist ] || { echo "Falta frontend/dist: ejecuta (con red) 'cd frontend && npm install && npm run build'"; exit 1; }
[ -x backend/.venv/bin/uvicorn ] || { echo "Falta backend/.venv: ejecuta (con red) 'cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'"; exit 1; }

mkdir -p data
cd backend
# Por defecto 127.0.0.1: datos de salud accesibles solo desde este equipo.
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PUERTO"
