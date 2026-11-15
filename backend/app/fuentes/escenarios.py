"""Escenarios guionizados para ensayar la demo de forma reproducible.

Usan los mismos servicios que la API real; no tocan la lógica clínica. Los valores son hipotéticos.
"""
from __future__ import annotations

import sqlite3

from ..repositorios import enlace as repo_enlace
from ..servicios import cola
from ..servicios import lecturas as servicio

NORMAL_T1 = (("frecuencia_respiratoria", 16), ("spo2", 98), ("presion_sistolica", 120),
             ("frecuencia_cardiaca", 70), ("temperatura", 36.8))

ESCENARIOS: dict[str, dict] = {
    "hipoxia_eclipse": {
        "descripcion": "T1 estable; se activa el modo eclipse; ocurre una hipoxia severa y una lectura rutinaria. "
                       "Nada sale hasta reconectar.",
        "pasos": [("enlace", True, "marte"),
                  *[("lectura", "T1", i, v) for i, v in NORMAL_T1],
                  ("enlace", False, "marte"),
                  ("lectura", "T1", "spo2", 88),
                  ("lectura", "T1", "temperatura", 36.9),
                  ("lectura", "T1", "frecuencia_cardiaca", 135)],
    },
    "co2_colectivo": {
        "descripcion": "CO2 de cabina elevado con dos tripulantes en deterioro: dispara la alerta colectiva.",
        "pasos": [("lectura", "T3", "co2", 3.6),
                  ("lectura", "T1", "spo2", 90),
                  ("lectura", "T2", "spo2", 92),
                  ("lectura", "T2", "frecuencia_respiratoria", 26)],
    },
    "o2_colectivo": {
        "descripcion": "Caída de O2 en cabina con dos tripulantes afectados: dispara la alerta colectiva de hipoxia ambiental.",
        "pasos": [("lectura", "T3", "o2_cabina", 19.1),
                  ("lectura", "T1", "spo2", 90),
                  ("lectura", "T2", "spo2", 92),
                  ("lectura", "T2", "frecuencia_respiratoria", 25)],
    },
    "proceso_infeccioso": {
        "descripcion": "Fiebre con taquicardia e hipotensión diastólica en T2: activa la regla combinada infecciosa y observación de perfusión.",
        "pasos": [("lectura", "T2", "temperatura", 38.4),
                  ("lectura", "T2", "frecuencia_cardiaca", 98),
                  ("lectura", "T2", "presion_sistolica", 114),
                  ("lectura", "T2", "presion_diastolica", 56)],
    },
}


def listar() -> list[dict]:
    return [{"id": k, "descripcion": v["descripcion"], "pasos": len(v["pasos"])} for k, v in ESCENARIOS.items()]


def ejecutar(conn: sqlite3.Connection, nombre: str, reconectar: bool = False) -> dict:
    if nombre not in ESCENARIOS:
        raise KeyError(nombre)
    registro = []
    for paso in ESCENARIOS[nombre]["pasos"]:
        if paso[0] == "lectura":
            _, tid, indicador, valor = paso
            r = servicio.registrar_lectura(conn, tid, indicador, valor, origen="simulado")
            registro.append({"paso": f"{tid} {indicador}={valor}", "nivel": r["nivel"], "prioridad": r["prioridad"]})
        else:
            _, activo, entorno = paso
            r = cola.cambiar_enlace(conn, activo, entorno)
            registro.append({"paso": f"enlace {'activo' if activo else 'ECLIPSE'} ({entorno})",
                             "despachados": len(r["despachados"])})
    if reconectar:
        entorno_actual = repo_enlace.leer(conn)["entorno"]
        r = cola.cambiar_enlace(conn, True, entorno_actual)
        registro.append({"paso": "reconexion", "despachados": len(r["despachados"]),
                         "orden_prioridades": [d["prioridad"] for d in r["despachados"]]})
    return {"escenario": nombre, "pasos": registro}
