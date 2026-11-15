"""Datos de demostración ficticios (no son personas reales)."""
import sys

from datetime import datetime, timezone

from ..repositorios import bienestar, perfil_ia, preferencias, seguridad as repo_seg, tripulantes
from ..servicios import auth

TRIPULANTES = [
    ("T1", "Valeria Montoya", "Comandante", "1985-03-12"),
    ("T2", "Mateo Ríos", "Especialista de misión", "1988-07-21"),
    ("T3", "Camila Ortega", "Ingeniero", "1990-11-02"),
    ("T4", "Andrés Leal", "Piloto", "1987-05-30"),
]
_NOMBRES_ANTIGUOS = {"T1": "Tripulante Uno", "T2": "Tripulante Dos", "T3": "Tripulante Tres", "T4": "Tripulante Cuatro"}

# Perfil FICTICIO de cada astronauta (no son personas reales; todo es simulado): lo que le gusta, cómo es y cómo prefiere
# que le hablen. Es lo que el asistente de cada quien usa para tratarlo. Cada persona puede cambiarlo desde su pantalla.
PERFILES = {
    "T1": {"intereses": "el ajedrez, salir a correr y tener metas claras",
           "rasgos": "Serena y disciplinada; lleva el peso de la tripulación y le cuesta pedir ayuda; prefiere que le hablen claro.",
           "tono": "directo", "detalle": "completo"},
    "T2": {"intereses": "tocar la guitarra, cocinar y hablar de su familia",
           "rasgos": "Curioso y bromista; se apaga si se siente aislado; le ayuda la conversación cálida.",
           "tono": "calido", "detalle": "completo"},
    "T3": {"intereses": "la ciencia ficción, la astronomía y los rompecabezas",
           "rasgos": "Analítica y tranquila; necesita silencio y pausas; prefiere respuestas breves y concretas.",
           "tono": "directo", "detalle": "breve"},
    "T4": {"intereses": "el fútbol, la música y los retos entre compañeros",
           "rasgos": "Sociable y competitivo; se anima con compañía y desafíos; el encierro le pesa.",
           "tono": "calido", "detalle": "breve"},
}

CREDENCIALES_DEMO = [
    ("T1", "comandante", "111111"),
    ("T2", "tripulante", "222222"),
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
     "Si el ánimo bajo persiste, conversa con un compañero o con el comandante. Es tu decisión."),
    ("crisis-anclaje", "crisis", "Anclaje inmediato 5-4-3-2-1",
     "Nombra en voz alta 5 cosas que ves en el módulo, 4 que puedes tocar, 3 sonidos, 2 olores y 1 respiración profunda."),
    ("crisis-acompanamiento", "crisis", "No permanezcas a solas",
     "Sal ahora a un módulo común o llama por el intercomunicador al comandante o a un compañero de confianza."),
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
    else:                                              # bases anteriores: solo se reemplazan los nombres genéricos de antes
        for tid, nombre, rol, _ in TRIPULANTES:
            conn.execute("UPDATE tripulantes SET nombre=? WHERE id=? AND nombre=?", (nombre, tid, _NOMBRES_ANTIGUOS[tid]))
            if tid == "T2":
                conn.execute("UPDATE tripulantes SET rol=? WHERE id='T2' AND rol='Médico de a bordo'", (rol,))
    ahora = datetime.now(timezone.utc).isoformat()
    for tid, perfil in PERFILES.items():               # solo si la persona aún no tiene perfil ni preferencias propias
        if tripulantes.existe(conn, tid) and not perfil_ia.existe(conn, tid):
            perfil_ia.guardar(conn, tid, perfil["intereses"], perfil["rasgos"], ahora)
        if tripulantes.existe(conn, tid) and preferencias.obtener(conn, tid) is None:
            preferencias.guardar(conn, tid, perfil["tono"], perfil["detalle"], "normal", ahora)
    bienestar.insertar_capsulas(conn, CAPSULAS)
    conn.commit()
    if "pytest" not in sys.modules:
        sembrar_credenciales_demo(conn)

