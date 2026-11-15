"""Datos de demostración ficticios (no son personas reales)."""
import sys

from ..repositorios import bienestar, seguridad as repo_seg, tripulantes
from ..servicios import auth

TRIPULANTES = [
    ("T1", "Tripulante Uno", "Comandante", "1985-03-12"),
    ("T2", "Tripulante Dos", "Médico de a bordo", "1988-07-21"),
    ("T3", "Tripulante Tres", "Ingeniero", "1990-11-02"),
    ("T4", "Tripulante Cuatro", "Piloto", "1987-05-30"),
]

CREDENCIALES_DEMO = [
    ("T1", "comandante", "111111"),
    ("T2", "medico", "222222"),
    ("T3", "tripulante", "333333"),
    ("T4", "tripulante", "444444"),
]

# Supuesto: contenido genérico de bienestar y contención en crisis; revisar con un profesional de salud mental.
CAPSULAS = [
    ("resp-lenta", "autorregulacion", "Respiración lenta",
     "Inhala 4 segundos, exhala 6 segundos. Repite durante 3 minutos."),
    ("rutina-sueno", "autorregulacion", "Rutina de descanso",
     "Mantén horarios fijos de descanso y reduce luz intensa antes de dormir."),
    ("contacto", "autorregulacion", "Habla con alguien de confianza",
     "Si el ánimo bajo persiste, conversa con un compañero o con el médico de a bordo. Es tu decisión."),
    ("crisis-anclaje", "crisis", "Anclaje inmediato 5-4-3-2-1",
     "Nombra en voz alta 5 cosas que ves en el módulo, 4 que puedes tocar, 3 sonidos, 2 olores y 1 respiración profunda."),
    ("crisis-acompanamiento", "crisis", "No permanezcas a solas",
     "Sal ahora a un módulo común o llama por el intercomunicador al médico de a bordo o a un compañero de confianza."),
    ("crisis-respiracion", "crisis", "Respiración de contención (4-7-8)",
     "Inhala por la nariz 4 segundos, sostén el aire 7 segundos y suelta despacio durante 8 segundos. Repite 4 ciclos."),
]


def sembrar_credenciales_demo(conn) -> None:
    for tid, rol, pin in CREDENCIALES_DEMO:
        if repo_seg.obtener_credencial(conn, tid) is None:
            auth.inscribir(conn, tid, rol, pin=pin)


def sembrar(conn) -> None:
    if tripulantes.contar(conn) == 0:
        tripulantes.insertar_varios(conn, TRIPULANTES)
    bienestar.insertar_capsulas(conn, CAPSULAS)
    conn.commit()
    if "pytest" not in sys.modules:
        sembrar_credenciales_demo(conn)

