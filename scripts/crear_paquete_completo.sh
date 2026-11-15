#!/usr/bin/env bash
# Crea el PAQUETE COMPLETO de este sistema: el ejecutable (con el motor de IA incrustado) + la carpeta `modelos/` con el modelo de IA,
# todo en un solo archivo comprimido que funciona sin internet y sin instalar nada. Pesa ~1.1 GB por el modelo.
# Uso: scripts/crear_paquete_completo.sh            (baja el modelo la primera vez)
#      MODELO_LOCAL=/ruta/modelo.gguf scripts/crear_paquete_completo.sh     (usa un .gguf que ya tengas)
# Requiere haber corrido scripts/crear_ejecutable.sh antes.
set -euo pipefail
cd "$(dirname "$0")/.."
MODELO_URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
ARCHIVO="qwen2.5-1.5b-instruct-q4_k_m.gguf"
cd dist-ejecutable
EXE=""; for c in orbit-health.exe orbit-health; do [ -f "$c" ] && EXE="$c" && break; done
[ -n "$EXE" ] || { echo "Primero corre scripts/crear_ejecutable.sh"; exit 1; }
mkdir -p modelos
if [ -n "${MODELO_LOCAL:-}" ]; then [ "$MODELO_LOCAL" -ef "modelos/$ARCHIVO" ] || cp "$MODELO_LOCAL" "modelos/$ARCHIVO"
elif [ ! -s "modelos/$ARCHIVO" ]; then curl -L --fail --retry 3 -C - -o "modelos/$ARCHIVO" "$MODELO_URL"; fi
TAM=$(wc -c < "modelos/$ARCHIVO"); [ "$TAM" -gt 500000000 ] || { echo "El modelo quedó incompleto ($TAM bytes)"; rm -f "modelos/$ARCHIVO"; exit 1; }
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) SO=windows; 7z a -tzip "orbit-health-$SO-completo.zip" "$EXE" modelos ./*.sha256 > /dev/null; SALIDA="orbit-health-$SO-completo.zip";;
  Darwin) SO=macos; tar czf "orbit-health-$SO-completo.tar.gz" "$EXE" modelos ./*.sha256; SALIDA="orbit-health-$SO-completo.tar.gz";;
  *) SO=linux; tar czf "orbit-health-$SO-completo.tar.gz" "$EXE" modelos ./*.sha256; SALIDA="orbit-health-$SO-completo.tar.gz";;
esac
echo "Listo: dist-ejecutable/$SALIDA ($(du -h "$SALIDA" | cut -f1))"
