#!/usr/bin/env bash
# Carga series BIDMC locales como historial de calibración (funciona SIN red).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
cd backend && exec .venv/bin/python -m app.fuentes.calibracion "$@"
