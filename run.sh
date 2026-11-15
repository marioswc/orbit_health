#!/usr/bin/env bash
# Arranque local de ORBIT Health. Requiere haber preparado dependencias (con red) una vez.
# En macOS (Darwin) abre automáticamente su ventana nativa de aplicación (con WebGL Metal, voz e IA local).
# Opciones:
#   ./run.sh              arranque nativo (en Mac abre ventana de aplicación vía scripts/lanzador.py)
#   ./run.sh --docker     arranca el contenedor con Docker Compose y abre la ventana nativa en el equipo anfitrión
#   ./run.sh --sin-ventana solo el servidor uvicorn en terminal, sin abrir ventana
set -euo pipefail
cd "$(dirname "$0")"
# .env solo rellena lo que NO está ya en el entorno (igual que el backend: el entorno gana).
if [ -f .env ]; then
  while IFS= read -r _l || [ -n "$_l" ]; do
    case "$_l" in ''|'#'*) continue;; esac
    _k="${_l%%=*}"; _k="${_k#export }"
    [ -z "${!_k+x}" ] && { set -a; eval "$_l"; set +a; }
  done < .env
fi
PUERTO="${ORBIT_PUERTO:-3000}"
HOST="${ORBIT_HOST:-127.0.0.1}"
MODO_DOCKER=0
SIN_VENTANA=0
for arg in "$@"; do
  case "$arg" in
    --docker) MODO_DOCKER=1 ;;
    --sin-ventana) SIN_VENTANA=1 ;;
  esac
done

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

if [ "$MODO_DOCKER" = "1" ]; then
  command -v docker >/dev/null || { echo "Falta Docker."; exit 1; }
  mkdir -p backend/models
  echo "Levantando ORBIT Health en Docker (http://127.0.0.1:$PUERTO)..."
  docker compose up --build -d
  for _ in $(seq 40); do
    curl -sf "http://127.0.0.1:$PUERTO/api/salud" >/dev/null 2>&1 && break
    sleep 0.5
  done
  if [ "$SIN_VENTANA" = "0" ]; then
    PY_HOST=$(command -v python3 || command -v python || true)
    [ -x backend/.venv/bin/python ] && PY_HOST="backend/.venv/bin/python"
    [ -n "$PY_HOST" ] && "$PY_HOST" scripts/lanzador.py --puerto "$PUERTO"
  fi
  echo "Contenedor activo. Mostrando registros (Ctrl+C para detener el contenedor)..."
  trap 'echo; echo "Deteniendo contenedor..."; docker compose stop' INT TERM
  docker compose logs -f
  exit 0
fi

[ -d frontend/dist ] || { echo "Falta frontend/dist: ejecuta (con red) 'cd frontend && npm install && npm run build'"; exit 1; }
[ -x backend/.venv/bin/uvicorn ] || { echo "Falta backend/.venv: ejecuta (con red) 'cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'"; exit 1; }

mkdir -p data
if [ "$(uname -s)" = "Darwin" ] && [ "$SIN_VENTANA" = "0" ] && { [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; }; then
  exec backend/.venv/bin/python scripts/lanzador.py --puerto "$PUERTO"
fi

cd backend
# Por defecto 127.0.0.1: datos de salud accesibles solo desde este equipo.
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PUERTO"
