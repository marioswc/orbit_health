#!/usr/bin/env bash
# Crea cuentas de DEMOSTRACIÓN (T1 comandante 111111, T2 médico 222222, T3 y T4 tripulantes 333333 y 444444).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
cd backend && exec .venv/bin/python -m app.fuentes.cuentas_demo
