#!/bin/sh
# Arranque del contenedor de ORBIT Health. Su trabajo es que NINGUNA variable se pierda ni se malinterprete en silencio.
set -eu
limpiar() { printf '%s' "$1" | sed -e "s/^[[:space:]\"']*//" -e "s/[[:space:]\"']*$//"; }   # `docker run --env-file` deja las comillas DENTRO del valor

HOST="$(limpiar "${ORBIT_CONTENEDOR_HOST:-0.0.0.0}")"     # dentro del contenedor se escucha en todas las interfaces; el acceso externo lo limita docker-compose.yml (127.0.0.1)
PORT="$(limpiar "${ORBIT_PUERTO:-3000}")"
case "$PORT" in ''|*[!0-9]*) echo "[ORBIT ERROR] ORBIT_PUERTO=$PORT no es un número de puerto válido." >&2; exit 2;; esac

# Si la imagen se construyó con IA o voz (CON_IA=1, CON_VOZ=1), se activan solas SIN pisar lo que la persona haya definido.
M=/opt/orbit-modelos
if [ -d "$M" ]; then
  GGUF="$(ls "$M"/*.gguf 2>/dev/null | head -1 || true)"
  if [ -n "$GGUF" ] && [ -z "${ORBIT_IA_MODELO_GGUF:-}" ]; then export ORBIT_IA_MODELO_GGUF="$GGUF"; : "${ORBIT_IA_PROVEEDOR:=local}"; export ORBIT_IA_PROVEEDOR; fi
  if [ -d "$M/whisper-small" ] && [ -z "${ORBIT_VOZ_STT_MODELO:-}" ]; then
    export ORBIT_VOZ_STT_MODELO="$M/whisper-small" ORBIT_VOZ_PIPER_BIN="${ORBIT_VOZ_PIPER_BIN:-piper}"
    export ORBIT_VOZ_PIPER_MODELO="${ORBIT_VOZ_PIPER_MODELO:-$M/es_MX-claude-high.onnx}" ORBIT_VOZ_PIPER_MODELO_EN="${ORBIT_VOZ_PIPER_MODELO_EN:-$M/en_US-lessac-medium.onnx}"
    : "${ORBIT_VOZ_ACTIVA:=1}"; export ORBIT_VOZ_ACTIVA
  fi
fi

python -m app.diagnostico --advertencias || true          # en los registros del contenedor: variables mal escritas, voz sin modelo, etc.
exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
