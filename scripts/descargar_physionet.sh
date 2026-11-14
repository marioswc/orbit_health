#!/usr/bin/env bash
# Descarga (CON RED, una sola vez) los CSV de numéricos de BIDMC v1.0.0 y verifica SHA-256.
# Después el cargador funciona sin internet. Fuente: https://physionet.org/content/bidmc/1.0.0/
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=data/physionet; U=https://physionet.org/files/bidmc/1.0.0
mkdir -p "$DEST"
curl -sfL --max-time 60 "$U/SHA256SUMS.txt" -o "$DEST/SHA256SUMS.txt"
for i in $(seq -w 1 53); do
  f="bidmc_${i}_Numerics.csv"
  [ -f "$DEST/$f" ] || curl -sfL --max-time 60 "$U/bidmc_csv/$f" -o "$DEST/$f"
  esperado=$(grep "bidmc_csv/$f\$" "$DEST/SHA256SUMS.txt" | cut -d' ' -f1)
  real=$(sha256sum "$DEST/$f" | cut -d' ' -f1)
  [ -n "$esperado" ] && [ "$esperado" = "$real" ] || { echo "Checksum inválido: $f"; rm -f "$DEST/$f"; exit 1; }
done
echo "OK: 53 archivos verificados en $DEST"
