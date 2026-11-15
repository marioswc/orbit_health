#!/usr/bin/env bash
# Prepara la VOZ sin internet en la misión: oír (faster-whisper) y hablar (Piper, voz es_MX). Requiere internet UNA vez.
# Deja los modelos en backend/models (fuera de git). Después añade a .env las líneas que imprime al final.
set -euo pipefail
cd "$(dirname "$0")/../backend"
[ -x .venv/bin/pip ] || { echo "Falta backend/.venv: créalo primero (ver README)."; exit 1; }
.venv/bin/pip install -q -r requirements-voice.txt
mkdir -p models
.venv/bin/python - <<'PY'
from huggingface_hub import hf_hub_download, snapshot_download
import shutil, pathlib
d = pathlib.Path("models")
for f in ("es/es_MX/claude/high/es_MX-claude-high.onnx", "es/es_MX/claude/high/es_MX-claude-high.onnx.json"):
    p = hf_hub_download("rhasspy/piper-voices", f, local_dir=str(d / "_tmp"))
    shutil.move(p, d / pathlib.Path(f).name)
shutil.rmtree(d / "_tmp", ignore_errors=True)
snapshot_download("Systran/faster-whisper-small", local_dir=str(d / "whisper-small"))   # ~0.5 GB
PY
cat <<'TXT'
Listo. En .env:
ORBIT_VOZ_ACTIVA=1
ORBIT_VOZ_STT_MODELO=./models/whisper-small
ORBIT_VOZ_STT_LOCAL_ONLY=1
ORBIT_VOZ_PIPER_BIN=./.venv/bin/piper
ORBIT_VOZ_PIPER_MODELO=./models/es_MX-claude-high.onnx
TXT
