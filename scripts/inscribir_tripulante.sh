#!/usr/bin/env bash
# Alta de credenciales de un tripulante. Uso: scripts/inscribir_tripulante.sh T1 comandante|medico|tripulante [PIN]
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
cd backend && exec .venv/bin/python -m app.fuentes.inscripcion "$@"
