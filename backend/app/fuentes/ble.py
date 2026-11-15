"""Intérprete del servicio estándar de frecuencia cardíaca de Bluetooth Low Energy (GATT 0x180D / 0x2A37).

Lo implementan muchos pulsómetros y algunas bandas. No requiere la librería BLE, así que se puede probar sin hardware.
Otros signos (SpO₂, temperatura, presión) de las bandas comerciales suelen usar protocolos propietarios que NO se
cubren aquí.
"""
from __future__ import annotations

import math
from typing import Sequence

from .. import config  # noqa: F401  (mantiene el paquete coherente con el resto de fuentes)
from ..dominio.catalogos import validar

SERVICIO_FC = "0000180d-0000-1000-8000-00805f9b34fb"
CARACTERISTICA_FC = "00002a37-0000-1000-8000-00805f9b34fb"
RR_MIN_MS = 240.0       # ~250 lpm
RR_MAX_MS = 3000.0      # ~20 lpm
SALTO_RR_MAX = 0.35     # descarta saltos >35% entre latidos consecutivos (artefacto de movimiento o ectopia)


def parsear_medicion_fc(datos: bytes) -> dict:
    """Decodifica una notificación de 'Heart Rate Measurement'.

    Devuelve {'fc': int, 'contacto': True|False|None, 'rr_ms': [..]}. `contacto` es None si el sensor no informa.
    Lanza ValueError si el paquete está vacío o truncado.
    """
    if not datos:
        raise ValueError("Paquete vacío")
    banderas = datos[0]
    formato_16 = bool(banderas & 0x01)
    contacto_soportado = bool(banderas & 0x04)
    contacto_detectado = bool(banderas & 0x02)
    hay_energia = bool(banderas & 0x08)
    hay_rr = bool(banderas & 0x10)

    i = 1
    largo_fc = 2 if formato_16 else 1
    if len(datos) < i + largo_fc:
        raise ValueError("Paquete truncado: falta la frecuencia cardíaca")
    fc = int.from_bytes(datos[i:i + largo_fc], "little")
    i += largo_fc
    if hay_energia:
        if len(datos) < i + 2:
            raise ValueError("Paquete truncado: falta la energía gastada")
        i += 2
    rr = []
    if hay_rr:
        while i + 1 < len(datos):
            rr.append(round(int.from_bytes(datos[i:i + 2], "little") / 1024 * 1000, 1))   # unidades de 1/1024 s
            i += 2
    return {"fc": fc, "contacto": contacto_detectado if contacto_soportado else None, "rr_ms": rr}


def muestra_valida(medicion: dict) -> float | None:
    """La FC que se puede enviar, o None si el sensor no está en contacto con la piel o el valor es imposible."""
    if medicion["contacto"] is False:
        return None
    return float(medicion["fc"]) if validar("frecuencia_cardiaca", medicion["fc"]) is None else None


def rr_validos(rr_ms: Sequence[float]) -> list[float]:
    """Filtra intervalos RR dentro del rango fisiológico humano (240 a 3000 ms)."""
    return [float(r) for r in rr_ms if RR_MIN_MS <= r <= RR_MAX_MS]


def calcular_rmssd(rr_ms: Sequence[float]) -> float | None:
    """Calcula la variabilidad cardíaca RMSSD (ms) a partir de intervalos RR consecutivos válidos.

    Ignora pares consecutivos con saltos > 35 % (artefactos de movimiento) y valida contra el catálogo.
    """
    limpios = rr_validos(rr_ms)
    if len(limpios) < 2:
        return None
    difs_cuad = [
        (b - a) ** 2
        for a, b in zip(limpios, limpios[1:])
        if abs(b - a) / max(a, b) <= SALTO_RR_MAX
    ]
    if not difs_cuad:
        return None
    rmssd = round(math.sqrt(sum(difs_cuad) / len(difs_cuad)), 1)
    return rmssd if validar("variabilidad_cardiaca", rmssd) is None else None


def extraer_muestras(medicion: dict, ventana_rr: list[float] | None = None,
                     min_rr: int = 2, max_rr: int = 30) -> list[dict]:
    """Convierte una notificación BLE en muestras listas para `/api/sensores/flujo/lote` (FC y RMSSD).

    Si se pasa `ventana_rr`, acumula los intervalos RR entre notificaciones sucesivas (hasta `max_rr`)
    y limpia la ventana si se pierde el contacto con la piel.
    """
    if medicion.get("contacto") is False:
        if ventana_rr is not None:
            ventana_rr.clear()
        return []
    fc = muestra_valida(medicion)
    if fc is None:
        return []
    muestras = [{"indicador": "frecuencia_cardiaca", "valor": fc}]
    nuevos = rr_validos(medicion.get("rr_ms", []))
    if not nuevos:
        return muestras
    if ventana_rr is not None:
        ventana_rr.extend(nuevos)
        if len(ventana_rr) > max_rr:
            del ventana_rr[:-max_rr]
        serie = ventana_rr
    else:
        serie = nuevos
    if len(serie) >= max(2, min_rr):
        rmssd = calcular_rmssd(serie)
        if rmssd is not None:
            muestras.append({"indicador": "variabilidad_cardiaca", "valor": rmssd})
    return muestras


def describir_gatt(servicios) -> dict:
    """Resume la tabla GATT de un dispositivo: qué servicios trae y si ofrece el estándar de frecuencia cardíaca.

    `servicios` es cualquier iterable de objetos con `uuid` y `characteristics` (cada una con `uuid` y `properties`),
    como el que entrega la librería BLE al conectar. Así se puede probar sin un dispositivo.
    """
    lineas, tiene_fc, notificables = [], False, []
    for sv in servicios:
        uuid = str(sv.uuid).lower()
        es_fc = uuid == SERVICIO_FC
        tiene_fc = tiene_fc or es_fc
        lineas.append(f"Servicio {uuid}" + ("   <- frecuencia cardíaca ESTÁNDAR" if es_fc else ""))
        for ch in sv.characteristics:
            props = ",".join(sorted(ch.properties))
            lineas.append(f"    {str(ch.uuid).lower()}  [{props}]")
            if {"notify", "indicate"} & set(ch.properties):
                notificables.append(str(ch.uuid).lower())
    return {"lineas": lineas, "tiene_frecuencia_estandar": tiene_fc, "notificables": notificables,
            "servicios": sum(1 for _ in lineas if _.startswith("Servicio"))}


def elegir_coincidencia(coincidencias: list, mas_cercana: bool = False) -> tuple[str, object]:
    """Decide qué dispositivo usar entre los que coinciden con un nombre, sin adivinar.

    `coincidencias` son tuplas (nombre, señal_dbm, direccion, objeto). Devuelve ("ninguna", None), ("unica", item) o
    ("ambigua", lista_ordenada_por_señal). Con varias coincidencias solo elige si se pide `mas_cercana` (la de señal
    más fuerte, que suele ser la que llevas puesta); si no, devuelve la lista para que lo decida la persona.
    """
    ordenadas = sorted(coincidencias, key=lambda c: c[1] if c[1] is not None else -999, reverse=True)
    if not ordenadas:
        return "ninguna", None
    if len(ordenadas) == 1 or mas_cercana:
        return "unica", ordenadas[0]
    return "ambigua", ordenadas
