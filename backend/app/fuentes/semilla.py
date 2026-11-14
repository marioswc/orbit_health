"""Datos de demostración ficticios (no son personas reales)."""
from ..repositorios import bienestar, tripulantes

TRIPULANTES = [
    ("T1", "Tripulante Uno", "Comandante", "1985-03-12"),
    ("T2", "Tripulante Dos", "Médico de a bordo", "1988-07-21"),
    ("T3", "Tripulante Tres", "Ingeniero", "1990-11-02"),
    ("T4", "Tripulante Cuatro", "Piloto", "1987-05-30"),
]

# Supuesto: contenido genérico de bienestar; revisar con un profesional de salud mental.
CAPSULAS = [
    ("resp-lenta", "autorregulacion", "Respiración lenta",
     "Inhala 4 segundos, exhala 6 segundos. Repite durante 3 minutos."),
    ("rutina-sueno", "autorregulacion", "Rutina de descanso",
     "Mantén horarios fijos de descanso y reduce luz intensa antes de dormir."),
    ("contacto", "autorregulacion", "Habla con alguien de confianza",
     "Si el ánimo bajo persiste, conversa con un compañero o con el médico de a bordo. Es tu decisión."),
]


def sembrar(conn) -> None:
    if tripulantes.contar(conn) == 0:
        tripulantes.insertar_varios(conn, TRIPULANTES)
    if bienestar.contar_capsulas(conn) == 0:
        bienestar.insertar_capsulas(conn, CAPSULAS)
    conn.commit()
