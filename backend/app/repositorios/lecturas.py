"""Acceso a datos: lecturas fisiológicas y ambientales."""
import sqlite3
from typing import Sequence


def insertar(conn: sqlite3.Connection, tid: str, indicador: str, valor: float, unidad: str,
             nivel: str, puntos: int, ts: str, origen: str = "manual") -> int:
    cur = conn.execute(
        """INSERT INTO lecturas (tripulante_id, indicador, valor, unidad, nivel, puntos_news2, origen, ts)
           VALUES (?,?,?,?,?,?,?,?)""",
        (tid, indicador, valor, unidad, nivel, puntos, origen, ts))
    return cur.lastrowid


def valores_recientes(conn: sqlite3.Connection, tid: str, indicadores: Sequence[str], desde: str) -> dict[str, float]:
    """Último valor de cada indicador dentro de la ventana."""
    if not indicadores:
        return {}
    marcadores = ",".join("?" * len(indicadores))
    filas = conn.execute(
        f"""SELECT indicador, valor FROM lecturas
            WHERE tripulante_id=? AND ts>=? AND indicador IN ({marcadores}) ORDER BY id ASC""",
        (tid, desde, *indicadores)).fetchall()
    return {f["indicador"]: f["valor"] for f in filas}


def ultimas_en_ventana(conn: sqlite3.Connection, tid: str, desde: str) -> list[dict]:
    """Última lectura completa de cada indicador dentro de la ventana."""
    filas = conn.execute(
        "SELECT indicador, valor, unidad, nivel, ts FROM lecturas WHERE tripulante_id=? AND ts>=? ORDER BY id ASC",
        (tid, desde)).fetchall()
    return list({f["indicador"]: dict(f) for f in filas}.values())


def ultimo_global(conn: sqlite3.Connection, indicador: str, desde: str) -> float | None:
    """Última lectura de un indicador entre todos los tripulantes (p. ej. CO2 de cabina)."""
    f = conn.execute("SELECT valor FROM lecturas WHERE indicador=? AND ts>=? ORDER BY id DESC LIMIT 1",
                     (indicador, desde)).fetchone()
    return f["valor"] if f else None


def serie(conn: sqlite3.Connection, tid: str, indicador: str, desde: str, limite: int) -> list[dict]:
    """Serie temporal de un indicador, de la más antigua a la más reciente, para graficar."""
    filas = conn.execute(
        """SELECT ts, valor, nivel, origen FROM (
               SELECT id, ts, valor, nivel, origen FROM lecturas
               WHERE tripulante_id=? AND indicador=? AND ts>=? ORDER BY id DESC LIMIT ?)
           ORDER BY id ASC""", (tid, indicador, desde, limite)).fetchall()
    return [dict(f) for f in filas]


def recientes(conn: sqlite3.Connection, tid: str, limite: int) -> list[dict]:
    """Últimas lecturas de un tripulante (más reciente primero)."""
    return [dict(f) for f in conn.execute(
        "SELECT ts, indicador, valor, unidad, nivel, origen FROM lecturas WHERE tripulante_id=? ORDER BY id DESC LIMIT ?",
        (tid, limite))]


def ultima_captura(conn: sqlite3.Connection, tid: str) -> str | None:
    """Hora de la última captura real. Las series de calibración son historia y no cuentan como medición."""
    f = conn.execute("SELECT MAX(ts) FROM lecturas WHERE tripulante_id=? AND origen!='calibracion'", (tid,)).fetchone()
    return f[0]


def indicadores_por_dia(conn: sqlite3.Connection, tid: str, indicadores: Sequence[str]) -> dict[str, set[str]]:
    """Para cada día (UTC) qué indicadores se registraron de verdad. La calibración es historia, no cuenta."""
    marcadores = ",".join("?" * len(indicadores))
    filas = conn.execute(
        f"""SELECT DISTINCT substr(ts, 1, 10) AS dia, indicador FROM lecturas
            WHERE tripulante_id=? AND origen!='calibracion' AND indicador IN ({marcadores})""", (tid, *indicadores)).fetchall()
    dias: dict[str, set[str]] = {}
    for f in filas:
        dias.setdefault(f["dia"], set()).add(f["indicador"])
    return dias


def historial_previo(conn: sqlite3.Connection, tid: str, indicador: str, desde: str, antes_de: str) -> list[float]:
    """Valores del indicador entre `desde` y antes de `antes_de` (excluye la propia lectura)."""
    return [f["valor"] for f in conn.execute(
        "SELECT valor FROM lecturas WHERE tripulante_id=? AND indicador=? AND ts>=? AND ts<?",
        (tid, indicador, desde, antes_de))]


def historial(conn: sqlite3.Connection, tid: str, indicador: str, desde: str) -> list[float]:
    return [f["valor"] for f in conn.execute(
        "SELECT valor FROM lecturas WHERE tripulante_id=? AND indicador=? AND ts>=?",
        (tid, indicador, desde))]
