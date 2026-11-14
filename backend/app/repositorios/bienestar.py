"""Acceso a datos: diario privado, tamizajes, cápsulas y avisos consentidos al médico. Nada toca la cola de salida."""
import sqlite3


def insertar_nota(conn: sqlite3.Connection, tid: str, titulo: str | None, contenido: str) -> int:
    return conn.execute(
        "INSERT INTO diario_privado (tripulante_id, titulo, contenido) VALUES (?,?,?)",
        (tid, titulo, contenido)).lastrowid


def listar_notas(conn: sqlite3.Connection, tid: str, limite: int = 50) -> list[dict]:
    return [dict(f) for f in conn.execute(
        "SELECT id, titulo, contenido, ts FROM diario_privado WHERE tripulante_id=? ORDER BY id DESC LIMIT ?",
        (tid, limite))]


def insertar_tamizaje(conn: sqlite3.Connection, tid: str, item1: int, item2: int, total: int,
                      riesgo_autolesion: bool = False, nivel_protocolo: str = "ninguno",
                      calidad_oxigeno: float | None = None) -> int:
    return conn.execute(
        """INSERT INTO tamizajes (tripulante_id, item1, item2, total, riesgo_autolesion, calidad_oxigeno, nivel_protocolo)
           VALUES (?,?,?,?,?,?,?)""",
        (tid, item1, item2, total, 1 if riesgo_autolesion else 0, calidad_oxigeno, nivel_protocolo),
    ).lastrowid


def obtener_tamizaje(conn: sqlite3.Connection, tamizaje_id: int) -> dict | None:
    f = conn.execute("SELECT * FROM tamizajes WHERE id=?", (tamizaje_id,)).fetchone()
    return dict(f) if f else None


def capsulas_por_categoria(conn: sqlite3.Connection, categoria: str) -> list[dict]:
    return [dict(c) for c in conn.execute(
        "SELECT id, categoria, titulo, contenido_markdown FROM capsulas WHERE categoria=?", (categoria,))]


def contar_capsulas(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM capsulas").fetchone()[0]


def insertar_capsulas(conn: sqlite3.Connection, filas: list[tuple]) -> None:
    conn.executemany("INSERT OR IGNORE INTO capsulas (id,categoria,titulo,contenido_markdown) VALUES (?,?,?,?)", filas)


def insertar_animo(conn: sqlite3.Connection, tid: str, valor: int, ts: str) -> int:
    return conn.execute("INSERT INTO animo_diario (tripulante_id, valor, ts) VALUES (?,?,?)", (tid, valor, ts)).lastrowid


def animo_desde(conn: sqlite3.Connection, tid: str, desde: str, antes_de: str | None = None) -> list[dict]:
    filtro, params = ("AND ts<?", (tid, desde, antes_de)) if antes_de else ("", (tid, desde))
    return [dict(f) for f in conn.execute(
        f"SELECT ts, valor FROM animo_diario WHERE tripulante_id=? AND ts>=? {filtro} ORDER BY id ASC", params)]


# ---- Avisos al médico de a bordo (solo con consentimiento explícito del propio tripulante) ----
def insertar_aviso_medico(conn: sqlite3.Connection, tid: str, tipo: str, nivel_protocolo: str,
                          tamizaje_id: int | None, mensaje_opcional: str | None, ts: str) -> int:
    return conn.execute(
        """INSERT INTO avisos_salud_mental
           (tripulante_id, tipo, nivel_protocolo, tamizaje_id, mensaje_opcional, consentimiento, estado, creado_ts, actualizado_ts)
           VALUES (?,?,?,?,?,1,'pendiente',?,?)""",
        (tid, tipo, nivel_protocolo, tamizaje_id, mensaje_opcional, ts, ts),
    ).lastrowid


def obtener_aviso_medico(conn: sqlite3.Connection, aviso_id: int) -> dict | None:
    f = conn.execute("SELECT * FROM avisos_salud_mental WHERE id=?", (aviso_id,)).fetchone()
    return dict(f) if f else None


def listar_avisos_de_tripulante(conn: sqlite3.Connection, tid: str, limite: int = 50) -> list[dict]:
    return [dict(f) for f in conn.execute(
        """SELECT id, tripulante_id, tipo, nivel_protocolo, tamizaje_id, mensaje_opcional,
                  estado, atendido_por, creado_ts, actualizado_ts
           FROM avisos_salud_mental WHERE tripulante_id=? ORDER BY id DESC LIMIT ?""",
        (tid, limite))]


def listar_avisos_para_medico(conn: sqlite3.Connection, solo_pendientes: bool = False, limite: int = 100) -> list[dict]:
    """Devuelve solo avisos con consentimiento vigente (excluye los revocados por su dueño)."""
    condicion = "a.consentimiento = 1 AND a.estado = 'pendiente'" if solo_pendientes else "a.consentimiento = 1 AND a.estado != 'revocado'"
    return [dict(f) for f in conn.execute(
        f"""SELECT a.id, a.tripulante_id, t.nombre AS tripulante_nombre, a.tipo, a.nivel_protocolo,
                   a.tamizaje_id, a.mensaje_opcional, a.estado, a.atendido_por, a.creado_ts, a.actualizado_ts
            FROM avisos_salud_mental a
            JOIN tripulantes t ON t.id = a.tripulante_id
            WHERE {condicion}
            ORDER BY CASE a.nivel_protocolo WHEN 'crisis' THEN 0 ELSE 1 END, a.id DESC
            LIMIT ?""",
        (limite,))]


def actualizar_estado_aviso(conn: sqlite3.Connection, aviso_id: int, estado: str,
                            ts: str, atendido_por: str | None = None) -> None:
    conn.execute(
        "UPDATE avisos_salud_mental SET estado=?, atendido_por=COALESCE(?, atendido_por), actualizado_ts=? WHERE id=?",
        (estado, atendido_por, ts, aviso_id),
    )
