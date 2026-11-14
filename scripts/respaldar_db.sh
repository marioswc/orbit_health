#!/usr/bin/env bash
# Respaldo consistente de la base (seguro con el servidor en marcha). Uso: scripts/respaldar_db.sh [carpeta]
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
cd backend && exec .venv/bin/python -m app.repositorios.respaldo "$@"
