"""Respaldo consistente de la base SQLite, seguro con el servidor en marcha."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .. import config


def respaldar(destino_dir: str | Path, origen: str | None = None, conservar: int = 10) -> Path:
    """Copia la base con la API de respaldo de SQLite, verifica su integridad y rota copias antiguas."""
    origen = origen or config.DB_PATH
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destino = destino_dir / f"orbit_health_{marca}.db"
    src = sqlite3.connect(origen)
    dst = sqlite3.connect(destino)
    try:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("El respaldo no pasó la verificación de integridad")
    except Exception:
        dst.close(); src.close(); destino.unlink(missing_ok=True)
        raise
    dst.close(); src.close()
    for vieja in sorted(destino_dir.glob("orbit_health_*.db"))[:-conservar]:
        vieja.unlink()
    return destino


if __name__ == "__main__":
    import sys
    print(respaldar(sys.argv[1] if len(sys.argv) > 1 else config.RAIZ / "data" / "respaldos"))
