"""Integridad de la cola de salida: hash encadenado verificable (lógica pura, sin base de datos).

hash = SHA-256(hash_prev | tripulante_id | tipo_evento | prioridad | payload | ts_guardado)
"""
from __future__ import annotations

import hashlib
from typing import Iterable, Mapping

GENESIS = "GENESIS"


def calcular_hash(prev: str, tripulante_id: str, tipo_evento: str,
                  prioridad: int, payload: str, ts_guardado: str) -> str:
    base = "|".join([prev, tripulante_id, tipo_evento, str(prioridad), payload, ts_guardado])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def verificar_filas(filas: Iterable[Mapping]) -> dict:
    """Recorre eventos en orden de id y confirma que la cadena no fue alterada."""
    prev = GENESIS
    total = 0
    for f in filas:
        total += 1
        esperado = calcular_hash(prev, f["tripulante_id"], f["tipo_evento"],
                                 f["prioridad"], f["payload"], f["ts_guardado"])
        if f["hash_prev"] != prev or f["hash"] != esperado:
            return {"valida": False, "total": total, "primer_invalido": f["id"]}
        prev = f["hash"]
    return {"valida": True, "total": total, "primer_invalido": None}
