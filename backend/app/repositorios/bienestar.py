"""Acceso a datos: diario privado, tamizajes y cápsulas. Nada de esto toca la cola de salida."""
import sqlite3


def insertar_nota(conn: sqlite3.Connection, tid: str, titulo: str | None, contenido: str) -> int:
    return conn.execute(
        "INSERT INTO diario_privado (tripulante_id, titulo, contenido) VALUES (?,?,?)",
        (tid, titulo, contenido)).lastrowid


def listar_notas(conn: sqlite3.Connection, tid: str, limite: int = 50) -> list[dict]:
    return [dict(f) for f in conn.execute(
        "SELECT id, titulo, contenido, ts FROM diario_privado WHERE tripulante_id=? ORDER BY id DESC LIMIT ?",
        (tid, limite))]


def insertar_tamizaje(conn: sqlite3.Connection, tid: str, item1: int, item2: int, total: int) -> None:
    conn.execute("INSERT INTO tamizajes (tripulante_id,item1,item2,total) VALUES (?,?,?,?)",
                 (tid, item1, item2, total))


def capsulas_por_categoria(conn: sqlite3.Connection, categoria: str) -> list[dict]:
    return [dict(c) for c in conn.execute(
        "SELECT id, categoria, titulo, contenido_markdown FROM capsulas WHERE categoria=?", (categoria,))]


def contar_capsulas(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM capsulas").fetchone()[0]


def insertar_capsulas(conn: sqlite3.Connection, filas: list[tuple]) -> None:
    conn.executemany("INSERT INTO capsulas (id,categoria,titulo,contenido_markdown) VALUES (?,?,?,?)", filas)
