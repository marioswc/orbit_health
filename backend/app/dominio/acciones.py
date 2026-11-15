"""Acciones sugeridas ante un resultado. Son pasos de PROCEDIMIENTO (repetir, avisar, volver a medir).

No contienen indicaciones de tratamiento ni de medicación: eso lo debe definir y validar un clínico.

El asistente se adapta al astronauta SOLO con preferencias que él elige (tono y detalle): cambia cómo se dice,
nunca qué se decide ni el nivel de alerta, y no deduce nada de su diario ni de su ánimo.
"""
from __future__ import annotations

from typing import Mapping, Sequence

TONOS = ("directo", "calido")
DETALLES = ("breve", "completo")
RECORDATORIOS = ("minimo", "normal", "frecuente")
ESTILO_POR_DEFECTO = {"tono": "directo", "detalle": "completo", "recordatorios": "normal"}

PLANTILLAS = {
    "repetir_ahora": {"directo": "Repite la medición ahora para descartar un error de captura o de sensor.",
                      "calido": "Vuelve a medir ahora, con calma, para descartar un error de captura o de sensor."},
    "avisar_urgente": {"directo": "Avisa de inmediato al comandante o a un compañero.",
                       "calido": "Avisa ahora al comandante o a un compañero: no tienes que resolverlo solo."},
    "cola_prioridad": {"directo": "El evento queda en la cola con prioridad máxima y saldrá primero en cuanto haya enlace.",
                       "calido": "Tu aviso ya está en la cola con la máxima prioridad y saldrá primero en cuanto haya enlace."},
    "repetir": {"directo": "Repite la medición para confirmarla.",
                "calido": "Vuelve a medir para confirmar el dato."},
    "avisar_si_persiste": {"directo": "Si se mantiene, avisa al comandante.",
                           "calido": "Si se mantiene, cuéntaselo al comandante o a un compañero de confianza."},
    "combinacion": {"directo": "Combinación detectada: {nombre}. Revisa ambos valores.",
                    "calido": "Detecté una combinación de valores: {nombre}. Revisa ambos con calma."},
    "observacion": {"directo": "Valor en observación: repite la medición en reposo y registra cómo evoluciona.",
                    "calido": "Este valor queda en observación: repite la medición en reposo y anota cómo evoluciona."},
    "linea_base": {"directo": "El valor se aleja de lo habitual de esta persona en los últimos 14 días.",
                   "calido": "Este valor se aleja de lo que suele ser habitual para esta persona en los últimos 14 días."},
    "faltantes": {"directo": "Faltan signos para una evaluación completa: {nombres}. Regístralos si puedes.",
                  "calido": "Para una evaluación más completa faltan: {nombres}. Si puedes, regístralos."},
    "proxima": {"directo": "Próxima captura recomendada en {n} min.",
                "calido": "Te sugiero volver a medir en {n} min."},
}

# En el modo breve solo quedan los pasos esenciales; las explicaciones se omiten, nunca los avisos.
ESENCIALES = {"repetir_ahora", "avisar_urgente", "repetir", "avisar_si_persiste", "combinacion", "proxima"}


def _minutos(n: float) -> str:
    return f"{int(n)}" if float(n).is_integer() else f"{n:g}"


def pasos_estructurados(nivel: str, proxima_captura_min: float, observacion: bool = False,
                        aviso_linea_base: bool = False, faltantes: Sequence[str] = (),
                        reglas: Sequence[Mapping] = (), etiquetas: Mapping[str, str] | None = None) -> list[dict]:
    """Qué hay que decir, sin decidir todavía cómo se dice."""
    etiquetas = etiquetas or {}
    pasos: list[dict] = []
    if nivel == "rojo":
        pasos += [{"clave": "repetir_ahora"}, {"clave": "avisar_urgente"}, {"clave": "cola_prioridad"}]
    elif nivel == "amarillo":
        pasos += [{"clave": "repetir"}, {"clave": "avisar_si_persiste"}]
    for r in reglas:
        pasos.append({"clave": "combinacion", "nombre": r["nombre"]})
    if observacion:
        pasos.append({"clave": "observacion"})
    if aviso_linea_base:
        pasos.append({"clave": "linea_base"})
    if faltantes and nivel != "verde":
        pasos.append({"clave": "faltantes", "nombres": ", ".join(etiquetas.get(f, f) for f in faltantes)})
    pasos.append({"clave": "proxima", "n": _minutos(proxima_captura_min)})
    return pasos


def renderizar(pasos: Sequence[Mapping], tono: str = "directo", detalle: str = "completo") -> list[str]:
    tono = tono if tono in TONOS else "directo"
    salida = []
    for p in pasos:
        if detalle == "breve" and p["clave"] not in ESENCIALES:
            continue
        salida.append(PLANTILLAS[p["clave"]][tono].format(**{k: v for k, v in p.items() if k != "clave"}))
    return salida


def ajustar_intervalo(minutos: float, nivel: str, recordatorios: str = "normal") -> float:
    """Aplica la preferencia de recordatorios sin poner en riesgo: 'minimo' solo alarga en verde."""
    if recordatorios == "frecuente":
        return max(1.0, minutos / 2)
    if recordatorios == "minimo" and nivel == "verde":
        return minutos * 1.5
    return minutos


def acciones_sugeridas(nivel: str, proxima_captura_min: float, observacion: bool = False,
                       aviso_linea_base: bool = False, faltantes: Sequence[str] = (),
                       reglas: Sequence[Mapping] = (), etiquetas: Mapping[str, str] | None = None,
                       tono: str = "directo", detalle: str = "completo") -> list[str]:
    return renderizar(pasos_estructurados(nivel, proxima_captura_min, observacion, aviso_linea_base,
                                          faltantes, reglas, etiquetas), tono, detalle)
