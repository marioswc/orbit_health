"""Acciones sugeridas ante un resultado. Son pasos de PROCEDIMIENTO (repetir, avisar, volver a medir).

No contienen indicaciones de tratamiento ni de medicación: eso lo debe definir y validar un clínico.
"""
from __future__ import annotations

from typing import Mapping, Sequence


def _minutos(n: float) -> str:
    return f"{int(n)}" if float(n).is_integer() else f"{n:g}"


def acciones_sugeridas(nivel: str, proxima_captura_min: float, observacion: bool = False,
                       aviso_linea_base: bool = False, faltantes: Sequence[str] = (),
                       reglas: Sequence[Mapping] = (), etiquetas: Mapping[str, str] | None = None) -> list[str]:
    etiquetas = etiquetas or {}
    pasos: list[str] = []
    if nivel == "rojo":
        pasos += ["Repite la medición ahora para descartar un error de captura o de sensor.",
                  "Avisa de inmediato al médico de a bordo o al comandante.",
                  "El evento queda en la cola con prioridad máxima y saldrá primero en cuanto haya enlace."]
    elif nivel == "amarillo":
        pasos += ["Repite la medición para confirmarla.",
                  "Si se mantiene, avisa al médico de a bordo."]
    for r in reglas:
        pasos.append(f"Combinación detectada: {r['nombre']}. Revisa ambos valores.")
    if observacion:
        pasos.append("Valor en observación: repite la medición en reposo y registra cómo evoluciona.")
    if aviso_linea_base:
        pasos.append("El valor se aleja de lo habitual de esta persona en los últimos 14 días.")
    if faltantes and nivel != "verde":
        nombres = ", ".join(etiquetas.get(f, f) for f in faltantes)
        pasos.append(f"Faltan signos para una evaluación completa: {nombres}. Regístralos si puedes.")
    pasos.append(f"Próxima captura recomendada en {_minutos(proxima_captura_min)} min.")
    return pasos
