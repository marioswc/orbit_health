"""Casos de uso de bienestar: diario y PHQ-2. Por diseño nada de esto se encola hacia Tierra."""
import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config
from ..dominio import reglas
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


def registrar_animo(conn: sqlite3.Connection, tid: str, valor: int) -> dict:
    """Ánimo diario 1 a 5. Privado: no se encola. Si es bajo o se aleja de lo habitual, ofrece apoyo."""
    ahora = datetime.now(timezone.utc)
    desde = (ahora - timedelta(days=config.DIAS_LINEA_BASE)).isoformat()
    previo = [p["valor"] for p in repo.animo_desde(conn, tid, desde)]
    linea = reglas.desviacion_linea_base(float(valor), previo)
    repo.insertar_animo(conn, tid, valor, ahora.isoformat())
    conn.commit()
    bajo = reglas.animo_bajo(valor)
    capsulas = repo.capsulas_por_categoria(conn, "autorregulacion") if (bajo or linea["aviso"]) else []
    return {"valor": valor, "bajo": bajo, "aviso_linea_base": linea["aviso"], "capsulas": capsulas,
            "privado": True, "transmitido_tierra": False}


def serie_animo(conn: sqlite3.Connection, tid: str, dias: float = 14) -> dict:
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    puntos = repo.animo_desde(conn, tid, desde)
    valores = [p["valor"] for p in puntos]
    return {"puntos": puntos, "media": round(sum(valores) / len(valores), 2) if valores else None, "privado": True}
