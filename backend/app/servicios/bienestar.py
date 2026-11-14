"""Casos de uso de bienestar: diario y PHQ-2. Por diseño nada de esto se encola hacia Tierra."""
import sqlite3

from ..repositorios import bienestar as repo

CORTE_PHQ2 = 3  # Supuesto: tamizaje positivo con total >= 3 (validar con salud mental)


def registrar_nota(conn: sqlite3.Connection, tid: str, titulo: str | None, contenido: str) -> dict:
    nota_id = repo.insertar_nota(conn, tid, titulo, contenido)
    conn.commit()
    return {"diario_id": nota_id, "privado": True, "transmitido_tierra": False}


def listar_notas(conn: sqlite3.Connection, tid: str) -> list[dict]:
    return repo.listar_notas(conn, tid)


def registrar_tamizaje(conn: sqlite3.Connection, tid: str, item1: int, item2: int) -> dict:
    total = item1 + item2
    repo.insertar_tamizaje(conn, tid, item1, item2, total)
    conn.commit()
    positivo = total >= CORTE_PHQ2
    capsulas = repo.capsulas_por_categoria(conn, "autorregulacion") if positivo else []
    return {"total": total, "positivo": positivo, "capsulas": capsulas, "transmitido_tierra": False}
