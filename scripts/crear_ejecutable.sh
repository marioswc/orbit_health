#!/usr/bin/env bash
# Crea el ejecutable de ESTE sistema operativo (Linux, Mac o Windows con Git Bash): un solo archivo, sin instalar Python ni Node.
# Salida: dist-ejecutable/orbit-health  (con su .sha256).  Uso: scripts/crear_ejecutable.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON=$(command -v python3 || command -v python || true)
[ -n "$PYTHON" ] || { echo "Falta Python"; exit 1; }
command -v npm >/dev/null || { echo "Falta npm (para compilar la interfaz)"; exit 1; }

echo "[1/4] Interfaz"
(cd frontend && { [ -f package-lock.json ] && npm ci --no-audit --no-fund || npm install --no-audit --no-fund; } && npm run build)

echo "[2/4] Entorno de construcción (aparte del de desarrollo)"
[ -d .venv-build ] || "$PYTHON" -m venv .venv-build
PY=.venv-build/bin/python; [ -x "$PY" ] || PY=.venv-build/Scripts/python.exe
"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q -r backend/requirements.txt pyinstaller

echo "[3/4] Empaquetando"
SEP=":"; ROOT="$PWD"; EXTRA=()
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) SEP=";"; ROOT="$(pwd -W)"                       # en Windows PyInstaller necesita rutas D:/...
                        EXTRA=(--windowed --icon "$ROOT/empaquetado/orbit.ico");;   # sin ventana negra: solo la ventana de ORBIT
  Darwin) EXTRA=(--icon "$PWD/empaquetado/orbit.icns");;                # en Mac se mantiene la terminal (un .app no se pudo probar)
esac
"$PY" -m PyInstaller --noconfirm --clean --onefile --name orbit-health \
  --distpath dist-ejecutable --workpath build/pyinstaller --specpath build \
  --paths backend \
  --add-data "$ROOT/backend/app/datos${SEP}app/datos" \
  --add-data "$ROOT/backend/app/repositorios/schema.sql${SEP}app/repositorios" \
  --add-data "$ROOT/frontend/dist${SEP}frontend/dist" \
  --collect-submodules uvicorn --collect-submodules app ${EXTRA[@]+"${EXTRA[@]}"} \
  --exclude-module tkinter --exclude-module faster_whisper --exclude-module bleak \
  scripts/lanzador.py

echo "[4/4] Huella de integridad"
cd dist-ejecutable
f=""; for c in orbit-health.exe orbit-health; do [ -f "$c" ] && f="$c" && break; done      # .exe primero: Git Bash en Windows resuelve "orbit-health" a ".exe"
[ -n "$f" ] || { echo "No se generó el ejecutable"; exit 1; }
(sha256sum "$f" 2>/dev/null || shasum -a 256 "$f") | tee "$f.sha256"
echo; echo "Listo: dist-ejecutable/$f  (doble clic, o ./$f desde la terminal)"
