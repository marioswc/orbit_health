#!/usr/bin/env bash
# Prepara la IA local SIN sudo: descarga Ollama en ~/.local/ollama y verifica su hash. Requiere internet UNA vez
# (después funciona sin red). No arranca nada: al final imprime los comandos.
# Uso: scripts/instalar_ia_local.sh [modelo]     (por defecto qwen2.5:1.5b; ~1 GB, corre en CPU)
set -euo pipefail
MODELO="${1:-qwen2.5:1.5b}"
DESTINO="${ORBIT_OLLAMA_DIR:-$HOME/.local/ollama}"
command -v zstd >/dev/null || { echo "Falta zstd (sudo apt install zstd)"; exit 1; }
mkdir -p "$DESTINO" && cd "$DESTINO"

info="$(curl -fsS https://api.github.com/repos/ollama/ollama/releases/latest)"
leer() { printf '%s' "$info" | python3 -c "import json,sys; d=json.load(sys.stdin); a=[x for x in d['assets'] if x['name']=='ollama-linux-amd64.tar.zst'][0]; print(a['$1'])"; }
url="$(leer browser_download_url)"; esperado="$(leer digest)"; esperado="${esperado#sha256:}"

if [ ! -x bin/ollama ]; then
  echo "Descargando Ollama (~1.5 GB)..."
  curl -fL --retry 3 -o ollama.tar.zst "$url"
  [ "$(sha256sum ollama.tar.zst | cut -d' ' -f1)" = "$esperado" ] || { echo "El hash no coincide: se borra la descarga."; rm -f ollama.tar.zst; exit 1; }
  zstd -dc ollama.tar.zst | tar -x && rm -f ollama.tar.zst
fi
echo "Ollama listo en $DESTINO. Siguientes pasos:"
echo "  OLLAMA_HOST=127.0.0.1:11434 $DESTINO/bin/ollama serve &      # déjalo corriendo (solo local)"
echo "  $DESTINO/bin/ollama pull $MODELO                            # requiere internet, una sola vez"
echo "Y en .env: ORBIT_IA_PROVEEDOR=local, ORBIT_IA_LOCAL_MODELO=$MODELO, ORBIT_IA_LOCAL_TIMEOUT_S=20"
