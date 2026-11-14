"""Acceso a datos: estado persistente del enlace con Tierra."""
import sqlite3


def leer(conn: sqlite3.Connection) -> dict:
    f = conn.execute("SELECT activo, entorno FROM estado_enlace WHERE id=1").fetchone()
    return {"activo": bool(f["activo"]), "entorno": f["entorno"]}


def guardar(conn: sqlite3.Connection, activo: bool, entorno: str) -> None:
    conn.execute("UPDATE estado_enlace SET activo=?, entorno=? WHERE id=1", (int(activo), entorno))
