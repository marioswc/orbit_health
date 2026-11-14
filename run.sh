#!/usr/bin/env bash
# Arranque local de ORBIT Health. Requiere haber preparado dependencias (con red) una vez.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }
PUERTO="${ORBIT_PUERTO:-3000}"
HOST="${ORBIT_HOST:-127.0.0.1}"

# Exponer el servicio en la red de la cabina requiere autenticación por tripulante (ORBIT_AUTH=1).
# Sin ella solo se permite con confirmación explícita, porque los datos de salud quedarían visibles
# para cualquier dispositivo conectado.
case "$HOST" in
  127.0.0.1|localhost|::1) ;;
  *) [ "${ORBIT_AUTH:-0}" = "1" ] || [ "${ORBIT_PERMITIR_RED:-0}" = "1" ] || {
       echo "ORBIT_HOST=$HOST expone los datos en la red."
       echo "Activa la autenticación con ORBIT_AUTH=1 (y da de alta a la tripulación con scripts/inscribir_tripulante.sh)."
       exit 1; } ;;
esac

[ -d frontend/dist ] || { echo "Falta frontend/dist: ejecuta (con red) 'cd frontend && npm install && npm run build'"; exit 1; }
[ -x backend/.venv/bin/uvicorn ] || { echo "Falta backend/.venv: ejecuta (con red) 'cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'"; exit 1; }

mkdir -p data
cd backend
# Por defecto 127.0.0.1: datos de salud accesibles solo desde este equipo.
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PUERTO"
