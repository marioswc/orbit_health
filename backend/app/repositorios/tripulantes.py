"""Acceso a datos: tripulantes."""
import sqlite3


def existe(conn: sqlite3.Connection, tid: str) -> bool:
    return conn.execute("SELECT 1 FROM tripulantes WHERE id=?", (tid,)).fetchone() is not None


def listar(conn: sqlite3.Connection) -> list[dict]:
    return [dict(f) for f in conn.execute("SELECT id, nombre, rol FROM tripulantes ORDER BY id")]


def ids(conn: sqlite3.Connection) -> list[str]:
    return [f["id"] for f in conn.execute("SELECT id FROM tripulantes ORDER BY id")]


def contar(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM tripulantes").fetchone()[0]


def insertar_varios(conn: sqlite3.Connection, filas: list[tuple]) -> None:
    conn.executemany("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES (?,?,?,?)", filas)
