"""Carga series públicas (BIDMC, PhysioNet) como historial de calibración.

Funciona sin red: lee los CSV locales de data/physionet. Cada lectura queda con
origen='calibracion' y no entra a la cola de salida. Los registros provienen de
pacientes críticos hospitalizados: sirven para dar variabilidad realista a la
demo y a las pruebas, no como línea base clínica de una persona sana.
"""
from __future__ import annotations

import csv
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config
from .db import get_conn, init_db
from .dominio import reglas as engine
from .dominio.catalogos import INDICADORES, validar

COLUMNAS = {"HR": "frecuencia_cardiaca", "RESP": "frecuencia_respiratoria", "SpO2": "spo2"}
VENTANA_S = 20          # una lectura por cada 20 s (mediana de la ventana)
MARGEN_RECIENTE_H = 2   # la calibración termina antes de la ventana NEWS2 para no contaminarla


def leer_numerics(ruta: Path) -> dict[str, list[float]]:
    """Devuelve, por indicador, la mediana de cada ventana de VENTANA_S segundos."""
    crudo: dict[str, list[list[float]]] = {k: [] for k in COLUMNAS.values()}
    with ruta.open(newline="", encoding="utf-8") as f:
        lector = csv.reader(f)
        cabecera = [c.strip() for c in next(lector)]
        indices = {col: cabecera.index(col) for col in COLUMNAS}
        for n, fila in enumerate(lector):
            for col, ind in COLUMNAS.items():
                try:
                    v = float(fila[indices[col]])
                except (ValueError, IndexError):
                    continue
                if validar(ind, v) is not None:
                    continue
                bloque = n // VENTANA_S
                lista = crudo[ind]
                while len(lista) <= bloque:
                    lista.append([])
                lista[bloque].append(v)
    return {ind: [statistics.median(b) for b in bloques if b] for ind, bloques in crudo.items()}


def cargar(tripulante_id: str, ruta: Path, db_path: str | None = None,
           ahora: datetime | None = None) -> int:
    """Reemplaza las lecturas de calibración del tripulante por las del CSV. Devuelve cuántas insertó."""
    ahora = ahora or datetime.now(timezone.utc)
    fin = ahora - timedelta(hours=MARGEN_RECIENTE_H)
    inicio = ahora - timedelta(days=config.DIAS_LINEA_BASE)
    series = leer_numerics(ruta)
    init_db(db_path)
    conn = get_conn(db_path)
    try:
        if conn.execute("SELECT 1 FROM tripulantes WHERE id=?", (tripulante_id,)).fetchone() is None:
            raise ValueError(f"Tripulante inexistente: {tripulante_id}")
        conn.execute("DELETE FROM lecturas WHERE tripulante_id=? AND origen='calibracion'", (tripulante_id,))
        total = 0
        for ind, valores in series.items():
            n = len(valores)
            for i, v in enumerate(valores):
                ts = inicio + (fin - inicio) * (i / max(n - 1, 1))
                r = engine.evaluar_news2({ind: v})
                conn.execute(
                    """INSERT INTO lecturas (tripulante_id, indicador, valor, unidad, nivel, puntos_news2, origen, ts)
                       VALUES (?,?,?,?,?,?, 'calibracion', ?)""",
                    (tripulante_id, ind, v, INDICADORES[ind][1], r.nivel, r.puntos, ts.isoformat()),
                )
                total += 1
        conn.commit()
        return total
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    """Uso: python -m app.calibracion [directorio_csv]. Asigna un registro por tripulante."""
    directorio = Path(argv[0]) if argv else config.RAIZ.parent / "data" / "physionet"
    archivos = sorted(directorio.glob("bidmc_*_Numerics.csv"))
    if not archivos:
        print(f"No hay CSV en {directorio}. Ejecuta scripts/descargar_physionet.sh (con red).")
        return 1
    init_db()
    conn = get_conn()
    ids = [f["id"] for f in conn.execute("SELECT id FROM tripulantes ORDER BY id")]
    conn.close()
    if not ids:
        print("No hay tripulantes. Arranca el servidor una vez (siembra demo) o créalos antes.")
        return 1
    for tid, archivo in zip(ids, archivos):
        n = cargar(tid, archivo)
        print(f"{tid}: {n} lecturas desde {archivo.name}")
    print("Fuente: BIDMC PPG and Respiration Dataset v1.0.0 (PhysioNet, ODC-By 1.0, DOI 10.13026/C2208R)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
