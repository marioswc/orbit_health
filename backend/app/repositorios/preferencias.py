"""Acceso a datos: preferencias del asistente, elegidas por cada tripulante."""
import sqlite3


def obtener(conn: sqlite3.Connection, tid: str) -> dict | None:
    f = conn.execute("SELECT tono, detalle, recordatorios FROM preferencias WHERE tripulante_id=?", (tid,)).fetchone()
    return dict(f) if f else None


def guardar(conn: sqlite3.Connection, tid: str, tono: str, detalle: str, recordatorios: str, ts: str) -> None:
    conn.execute(
        """INSERT INTO preferencias (tripulante_id, tono, detalle, recordatorios, actualizado_ts) VALUES (?,?,?,?,?)
           ON CONFLICT(tripulante_id) DO UPDATE SET tono=excluded.tono, detalle=excluded.detalle,
           recordatorios=excluded.recordatorios, actualizado_ts=excluded.actualizado_ts""",
        (tid, tono, detalle, recordatorios, ts))
