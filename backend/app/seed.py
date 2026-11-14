"""Datos de demostración ficticios (no son personas reales)."""
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
    if conn.execute("SELECT COUNT(*) FROM tripulantes").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES (?,?,?,?)", TRIPULANTES)
    if conn.execute("SELECT COUNT(*) FROM capsulas").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO capsulas (id,categoria,titulo,contenido_markdown) VALUES (?,?,?,?)", CAPSULAS)
    conn.commit()
