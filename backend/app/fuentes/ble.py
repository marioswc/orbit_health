"""Intérprete del servicio estándar de frecuencia cardíaca de Bluetooth Low Energy (GATT 0x180D / 0x2A37).

Lo implementan muchos pulsómetros y algunas bandas. No requiere la librería BLE, así que se puede probar sin hardware.
Otros signos (SpO₂, temperatura, presión) de las bandas comerciales suelen usar protocolos propietarios que NO se
cubren aquí.
"""
from __future__ import annotations

from .. import config  # noqa: F401  (mantiene el paquete coherente con el resto de fuentes)
from ..dominio.catalogos import validar

SERVICIO_FC = "0000180d-0000-1000-8000-00805f9b34fb"
CARACTERISTICA_FC = "00002a37-0000-1000-8000-00805f9b34fb"


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
