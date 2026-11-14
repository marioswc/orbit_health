#!/usr/bin/env python3
"""Regenera docs/API_REFERENCIA.md desde el código. Uso: backend/.venv/bin/python scripts/generar_api_doc.py"""
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
tmp = tempfile.mkdtemp()                                   # no toca la base real
os.environ.update(ORBIT_DB_PATH=f"{tmp}/doc.db", ORBIT_DIR_RESPALDOS=f"{tmp}/r", ORBIT_RESPALDO_CADA_MIN="0",
                  ORBIT_SEED_DEMO="0", ORBIT_DEMO_API="1")

from app import main  # noqa: E402
from app.api.referencia import generar_markdown  # noqa: E402

destino = RAIZ / "docs" / "API_REFERENCIA.md"
destino.write_text(generar_markdown(main.app), encoding="utf-8")
print(f"Generado {destino.relative_to(RAIZ)}")
