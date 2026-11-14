"""Acceso a datos: credenciales, sesiones y auditoría."""
import sqlite3


def insertar_credencial(conn, tid, rol, pin_salt, pin_hash, recup_salt, recup_hash, ts) -> None:
    conn.execute(
        """INSERT INTO credenciales (tripulante_id, rol, pin_salt, pin_hash, recup_salt, recup_hash, actualizado_ts)
           VALUES (?,?,?,?,?,?,?)""", (tid, rol, pin_salt, pin_hash, recup_salt, recup_hash, ts))


def obtener_credencial(conn: sqlite3.Connection, tid: str) -> dict | None:
    f = conn.execute("SELECT * FROM credenciales WHERE tripulante_id=?", (tid,)).fetchone()
    return dict(f) if f else None


def cambiar_pin(conn, tid, pin_salt, pin_hash, ts, recup_salt=None, recup_hash=None) -> None:
    if recup_salt:
        conn.execute(
            """UPDATE credenciales SET pin_salt=?, pin_hash=?, recup_salt=?, recup_hash=?,
               intentos_fallidos=0, bloqueado_hasta=NULL, actualizado_ts=? WHERE tripulante_id=?""",
            (pin_salt, pin_hash, recup_salt, recup_hash, ts, tid))
    else:
        conn.execute(
            """UPDATE credenciales SET pin_salt=?, pin_hash=?, intentos_fallidos=0, bloqueado_hasta=NULL,
               actualizado_ts=? WHERE tripulante_id=?""", (pin_salt, pin_hash, ts, tid))


def guardar_intentos(conn, tid, intentos: int, bloqueado_hasta: str | None) -> None:
    conn.execute("UPDATE credenciales SET intentos_fallidos=?, bloqueado_hasta=? WHERE tripulante_id=?",
                 (intentos, bloqueado_hasta, tid))


def insertar_sesion(conn, token_hash, tid, creada, expira) -> None:
    conn.execute("INSERT INTO sesiones (token_hash, tripulante_id, creada_ts, expira_ts) VALUES (?,?,?,?)",
                 (token_hash, tid, creada, expira))


def obtener_sesion(conn, token_hash) -> dict | None:
    f = conn.execute(
        """SELECT s.tripulante_id, s.expira_ts, s.revocada, c.rol FROM sesiones s
           JOIN credenciales c ON c.tripulante_id = s.tripulante_id WHERE s.token_hash=?""",
        (token_hash,)).fetchone()
    return dict(f) if f else None


def revocar_sesion(conn, token_hash) -> None:
    conn.execute("UPDATE sesiones SET revocada=1 WHERE token_hash=?", (token_hash,))


def revocar_sesiones_de(conn, tid) -> None:
    conn.execute("UPDATE sesiones SET revocada=1 WHERE tripulante_id=?", (tid,))


# ---- auditoría ----
def auditoria_ultimo_hash(conn) -> str | None:
    f = conn.execute("SELECT hash FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
    return f["hash"] if f else None


def auditoria_insertar(conn, actor, accion, payload, ts, hash_prev, hash_) -> int:
    return conn.execute(
        """INSERT INTO auditoria (tripulante_id, tipo_evento, payload, ts_guardado, hash_prev, hash)
           VALUES (?,?,?,?,?,?)""", (actor, accion, payload, ts, hash_prev, hash_)).lastrowid


def auditoria_todos(conn):
    return conn.execute("SELECT * FROM auditoria ORDER BY id ASC")


def auditoria_recientes(conn, limite=100) -> list[dict]:
    return [dict(f) for f in conn.execute(
        "SELECT id, tripulante_id AS actor, tipo_evento AS accion, payload, ts_guardado AS ts FROM auditoria ORDER BY id DESC LIMIT ?",
        (limite,))]
