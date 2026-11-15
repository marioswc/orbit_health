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
           WHERE estado='retenido' AND resumido=0 ORDER BY prioridad ASC, id ASC""")]


def rutina_retenida(conn: sqlite3.Connection) -> list[dict]:
    """Eventos retenidos de prioridad 3 (rutina), del más antiguo al más nuevo."""
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, ts_guardado FROM cola_salida
           WHERE estado='retenido' AND resumido=0 AND prioridad=3 AND tipo_evento!='resumen_rutina' ORDER BY id ASC""")]


def marcar_resumidos(conn: sqlite3.Connection, ids: list[int]) -> None:
    """No borra nada: el evento sigue en la cadena y a bordo, solo deja de enviarse por separado."""
    conn.executemany("UPDATE cola_salida SET resumido=1 WHERE id=?", [(i,) for i in ids])


def en_transito_ordenados(conn: sqlite3.Connection) -> list[dict]:
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad, transmitido_ts, llegada_estimada_ts
           FROM cola_salida WHERE estado='en_transito' ORDER BY prioridad ASC, id ASC""")]


def conteo_por_estado_y_prioridad(conn: sqlite3.Connection) -> list[dict]:
    return [dict(f) for f in conn.execute(
        "SELECT estado, prioridad, COUNT(*) AS total FROM cola_salida WHERE resumido=0 GROUP BY estado, prioridad")]


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


def total_resumidos(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM cola_salida WHERE resumido=1").fetchone()[0]


def conteo_por_estado(conn: sqlite3.Connection, tid: str) -> dict:
    return {f["estado"]: f["n"] for f in conn.execute(
        "SELECT estado, COUNT(*) AS n FROM cola_salida WHERE tripulante_id=? GROUP BY estado", (tid,))}


def llegados(conn: sqlite3.Connection, ahora_iso: str, limite: int) -> list[dict]:
    """Eventos que, por la hora estimada, ya llegaron a Tierra. Solo lectura: no cambia ningún estado."""
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, tipo_evento, prioridad, payload, hash, transmitido_ts, llegada_estimada_ts,
                  ack_estimado_ts
           FROM cola_salida WHERE llegada_estimada_ts IS NOT NULL AND llegada_estimada_ts<=?
           ORDER BY prioridad ASC, id ASC LIMIT ?""", (ahora_iso, limite))]


def en_camino(conn: sqlite3.Connection, ahora_iso: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM cola_salida WHERE llegada_estimada_ts IS NOT NULL AND llegada_estimada_ts>?",
        (ahora_iso,)).fetchone()[0]


def retenidos(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM cola_salida WHERE estado='retenido' AND resumido=0").fetchone()[0]
