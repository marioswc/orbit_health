"""Acceso a datos: perfil personal del asistente (intereses y rasgos que la persona escribe)."""
import sqlite3


def obtener(conn: sqlite3.Connection, tid: str) -> dict:
    f = conn.execute("SELECT intereses, rasgos FROM perfil_ia WHERE tripulante_id=?", (tid,)).fetchone()
    return dict(f) if f else {"intereses": "", "rasgos": ""}


def existe(conn: sqlite3.Connection, tid: str) -> bool:
    return conn.execute("SELECT 1 FROM perfil_ia WHERE tripulante_id=?", (tid,)).fetchone() is not None


def guardar(conn: sqlite3.Connection, tid: str, intereses: str, rasgos: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO perfil_ia (tripulante_id, intereses, rasgos, actualizado_ts) VALUES (?,?,?,?)
           ON CONFLICT(tripulante_id) DO UPDATE SET intereses=excluded.intereses, rasgos=excluded.rasgos,
           actualizado_ts=excluded.actualizado_ts""",
        (tid, intereses, rasgos, ts))
