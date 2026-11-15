#!/usr/bin/env bash
# Deja ORBIT Health listo para usarse en una máquina nueva. Necesita internet UNA vez; después todo funciona sin red.
# Uso: scripts/preparar.sh        y luego:   ./run.sh      (abre http://127.0.0.1:3000)
set -euo pipefail
cd "$(dirname "$0")/.."

command -v python3 >/dev/null || { echo "Falta python3 (3.10 o superior)."; exit 1; }
command -v node >/dev/null && command -v npm >/dev/null || { echo "Falta Node.js con npm (para compilar la interfaz)."; exit 1; }

echo "[1/4] Backend: entorno de Python y dependencias"
[ -x backend/.venv/bin/python ] || python3 -m venv backend/.venv
backend/.venv/bin/pip install -q -r backend/requirements.txt

echo "[2/4] Frontend: dependencias y compilación"
(cd frontend && { [ -f package-lock.json ] && npm ci --no-audit --no-fund || npm install --no-audit --no-fund; } && npm run build)

echo "[3/4] Configuración (.env)"
if [ ! -f .env ]; then
  cp .env.example .env && chmod 600 .env
  echo "  .env creado desde .env.example (sin claves). Las claves, si las hay, van solo ahí."
else
  echo "  .env ya existe: no se toca."
fi

echo "[4/4] Comprobación rápida"
(cd backend && .venv/bin/python -c "from app import main; print('  backend importa bien')")
[ -f frontend/dist/index.html ] && echo "  interfaz compilada"

cat <<'TXT'

Listo. Para arrancar:            ./run.sh                 (http://127.0.0.1:3000, sin internet)
Cuentas de demostración con PIN: scripts/cuentas_demo.sh  (y ORBIT_AUTH=1 en .env)
IA local sin internet (opcional): scripts/instalar_ia_local.sh y scripts/instalar_voz_local.sh
Auditoría de seguridad:          backend/.venv/bin/python scripts/auditoria_seguridad.py
TXT
