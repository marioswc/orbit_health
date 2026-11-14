"""Acceso a datos: cola de salida (store-and-forward)."""
import sqlite3


def ultimo_hash(conn: sqlite3.Connection) -> str | None:
    f = conn.execute("SELECT hash FROM cola_salida ORDER BY id DESC LIMIT 1").fetchone()
    return f["hash"] if f else None


def insertar(conn: sqlite3.Connection, tid: str, tipo: str, prioridad: int, payload: str,
             ts_guardado: str, hash_prev: str, hash_: str) -> int:
    cur = conn.execute(
        """INSERT INTO cola_salida
           (tripulante_id, tipo_evento, prioridad, payload, ts_guardado, hash_prev, hash)
           VALUES (?,?,?,?,?,?,?)""",
        (tid, tipo, prioridad, payload, ts_guardado, hash_prev, hash_))
    return cur.lastrowid


def retenidos_ordenados(conn: sqlite3.Connection) -> list[dict]:
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad FROM cola_salida
           WHERE estado='retenido' ORDER BY prioridad ASC, id ASC""")]


def marcar_en_transito(conn: sqlite3.Connection, evento_id: int, transmitido: str, llegada: str,
                       ack: str | None = None) -> None:
    conn.execute(
        """UPDATE cola_salida SET estado='en_transito', transmitido_ts=?, llegada_estimada_ts=?,
           ack_estimado_ts=? WHERE id=?""",
        (transmitido, llegada, ack, evento_id))


def marcar_recibidos(conn: sqlite3.Connection, ahora_iso: str) -> int:
    return conn.execute(
        "UPDATE cola_salida SET estado='recibido' WHERE estado='en_transito' AND llegada_estimada_ts<=?",
        (ahora_iso,)).rowcount


def todos_en_orden(conn: sqlite3.Connection):
    return conn.execute("SELECT * FROM cola_salida ORDER BY id ASC")


def recientes(conn: sqlite3.Connection, limite: int = 200) -> list[dict]:
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad, estado, hash, ts_guardado,
                  transmitido_ts, llegada_estimada_ts, ack_estimado_ts
           FROM cola_salida ORDER BY id DESC LIMIT ?""", (limite,))]
