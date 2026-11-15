#!/usr/bin/env bash
# Borra SOLO lo regenerable (cachés y carpetas temporales de compilación).
# No toca: .env, backend/models, .venv, node_modules, data/, dist-ejecutable/.
# Con --todo también borra build/ y .venv-build/ (la próxima compilación tarda más).
set -euo pipefail
cd "$(dirname "$0")/.."
find . -path ./frontend/node_modules -prune -o -path ./backend/.venv -prune -o -path ./.venv-build -prune -o \
  -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .vite -o -name .mypy_cache \) -prune -exec rm -rf {} +
[ "${1:-}" = "--todo" ] && rm -rf build .venv-build frontend/dist
echo "Limpieza lista."
