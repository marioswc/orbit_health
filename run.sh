#!/usr/bin/env bash
# Arranque local de ORBIT Health. Requiere haber preparado dependencias (con red) una vez.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }
PUERTO="${ORBIT_PUERTO:-3000}"

[ -d frontend/dist ] || { echo "Falta frontend/dist: ejecuta (con red) 'cd frontend && npm install && npm run build'"; exit 1; }
[ -x backend/.venv/bin/uvicorn ] || { echo "Falta backend/.venv: ejecuta (con red) 'cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'"; exit 1; }

mkdir -p data
cd backend
# 127.0.0.1: datos de salud accesibles solo desde este equipo, no desde la red local.
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PUERTO"
