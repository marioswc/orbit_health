"""Autorrecuperación de la base: verifica al arrancar y, si está dañada, restaura el último respaldo bueno.

A bordo no hay quien repare el sistema. Nada se borra: la base dañada se conserva aparte como evidencia.
"""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .. import config
from ..repositorios import respaldo


def verificar(ruta: str | Path) -> tuple[bool, str]:
    """(ok, detalle). Detecta archivo inexistente, no SQLite o con corrupción interna."""
    ruta = Path(ruta)
    if not ruta.exists():
        return False, "no existe"
    try:
        c = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
        try:
            resultado = c.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            c.close()
    except sqlite3.DatabaseError as e:
        return False, str(e)
    return (resultado == "ok", resultado)


def _respaldos(directorio: Path) -> list[Path]:
    return sorted(directorio.glob("orbit_health_*.db"), reverse=True)


def ultimo_respaldo(directorio: str | Path | None = None) -> Path | None:
    lista = _respaldos(Path(directorio or config.DIR_RESPALDOS))
    return lista[0] if lista else None


def arranque_seguro(db_path: str | None = None, dir_respaldos: str | Path | None = None) -> dict:
    """Garantiza una base utilizable antes de arrancar. Nunca lanza: el sistema debe poder iniciar."""
    db = Path(db_path or config.DB_PATH)
    dirr = Path(dir_respaldos or config.DIR_RESPALDOS)
    if not db.exists():
        return {"estado": "nueva", "detalle": "No había base; se creará una nueva"}
    ok, detalle = verificar(db)
    if ok:
        return {"estado": "sana", "detalle": "Base verificada"}

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    aparte = db.with_name(f"{db.name}.danada-{marca}")
    for extra in ("", "-wal", "-shm"):                      # se conserva todo como evidencia
        origen = Path(str(db) + extra)
        if origen.exists():
            shutil.move(str(origen), str(aparte) + extra)

    for candidato in _respaldos(dirr):
        buena, _ = verificar(candidato)
        if not buena:
            continue
        src = sqlite3.connect(f"file:{candidato}?mode=ro", uri=True)
        dst = sqlite3.connect(db)
        try:
            src.backup(dst)
        finally:
            dst.close(); src.close()
        return {"estado": "restaurada", "detalle": f"Base dañada ({detalle}); restaurada desde {candidato.name}",
                "respaldo": candidato.name, "base_danada": aparte.name}
    return {"estado": "reiniciada",
            "detalle": f"Base dañada ({detalle}) y sin respaldo válido; se creó una base nueva",
            "base_danada": aparte.name}


def estado_salud(db_path: str | None = None, arranque: dict | None = None) -> dict:
    ok, detalle = verificar(db_path or config.DB_PATH)
    ultimo = ultimo_respaldo()
    return {
        "base_ok": ok, "detalle": detalle,
        "arranque": arranque,
        "respaldos": len(_respaldos(Path(config.DIR_RESPALDOS))),
        "ultimo_respaldo": ultimo.name if ultimo else None,
        "respaldo_cada_min": config.RESPALDO_CADA_MIN,
    }


def hacer_respaldo() -> Path:
    return respaldo.respaldar(config.DIR_RESPALDOS, conservar=config.RESPALDOS_CONSERVAR)
