"""Acceso a datos: perfil personal del asistente (intereses y motivadores que la persona escribe)."""
import sqlite3


def obtener(conn: sqlite3.Connection, tid: str) -> str:
    f = conn.execute("SELECT intereses FROM perfil_ia WHERE tripulante_id=?", (tid,)).fetchone()
    return f["intereses"] if f else ""


def guardar(conn: sqlite3.Connection, tid: str, intereses: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO perfil_ia (tripulante_id, intereses, actualizado_ts) VALUES (?,?,?)
           ON CONFLICT(tripulante_id) DO UPDATE SET intereses=excluded.intereses, actualizado_ts=excluded.actualizado_ts""",
        (tid, intereses, ts))
