"""Protecciones para cualquier texto que produzca un modelo de lenguaje. Lógica pura, sin red ni modelo.

Principio: el modelo nunca es la última palabra. Una crisis la atiende siempre el protocolo escrito, y todo lo que el
modelo diga se comprueba antes de mostrarse; si no pasa, se usa el texto determinista.

- `detectar_crisis`: frases de autolesión o suicidio. Es deliberadamente sensible: preferimos mostrar el protocolo de
  apoyo de más que dejar pasar una crisis a un modelo.
- `validar_respuesta`: rechaza números que no estén en el contexto, menciones de medicación o fármacos, enlaces,
  niveles de alerta que no corresponden y respuestas demasiado largas.
"""
from __future__ import annotations

import json
import re
import unicodedata

MAX_CARACTERES = 900
NIVELES = ("verde", "amarillo", "rojo")

# Todas en minúsculas y sin acentos (el texto se normaliza igual antes de comparar).
FRASES_DE_CRISIS = (
    "suicid", "quitarme la vida", "quitarse la vida", "matarme", "me voy a matar", "hacerme dano", "me hago dano", "me haga dano", "hacer dano a mi mismo", "me quiero hacer dano", "me voy a hacer dano", "lastimarme",
    "cortarme las venas", "no quiero vivir", "ya no quiero vivir", "quiero morir", "quisiera morir", "mejor muerto",
    "acabar con mi vida", "acabar con todo", "terminar con mi vida", "no vale la pena vivir", "no vale la pena seguir",
    "desaparecer para siempre", "no aguanto mas",
    "kill myself", "end my life", "want to die", "hurt myself", "self harm", "self-harm",
)

# Raíces de medicamentos y vías de administración: el sistema no da indicaciones de tratamiento.
RAICES_DE_MEDICACION = (
    "medicament", "farmac", "dosis", "pastilla", "tableta", "inyecc", "receta", "antibiotic", "analgesic",
    "ibuprofen", "paracetamol", "aspirin", "antidepresiv", "ansiolitic", "sedante", "antihistamin", "insulina",
    "oxigeno suplementario", "antiinflamator",
    "medication", "medicine", "prescri", "painkiller", "antibiotic", "antidepress", "sedative", "tranquiliz", "pill", "dosage",
)

# Colores de alerta en inglés -> el equivalente en español que usa el sistema.
NIVELES_EN = {"green": "verde", "yellow": "amarillo", "red": "rojo"}


def normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_acentos if unicodedata.category(c) != "Mn")


def detectar_crisis(texto: str) -> bool:
    """True si el texto sugiere autolesión o suicidio. Ante la duda, True."""
    t = normalizar(texto or "")
    return any(f in t for f in FRASES_DE_CRISIS)


# Un número que no es parte de un identificador (NEWS2, SpO2, T1 no cuentan).
_NUMERO = re.compile(r"(?<![A-Za-z0-9_])\d+(?:[.,]\d+)?(?![A-Za-z0-9_])")


def _numeros(texto: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUMERO.findall(texto)}


def _niveles_permitidos(contexto) -> set[str]:
    return {n for n in NIVELES if f'"{n}"' in json.dumps(contexto, ensure_ascii=False, default=str)}


def validar_respuesta(texto: str | None, contexto, pregunta: str = "", secretos: tuple[str, ...] = ()) -> tuple[bool, str]:
    """(ok, motivo). `contexto` es el estado ya calculado; `pregunta` es lo que dijo el usuario (si lo hubo)."""
    if not texto or not texto.strip():
        return False, "respuesta vacía"
    if len(texto) > MAX_CARACTERES:
        return False, "respuesta demasiado larga"
    t = normalizar(texto)
    if _filtra_instrucciones(t, secretos):
        return False, "filtra sus instrucciones internas"
    if "http://" in t or "https://" in t or "www." in t:
        return False, "contiene un enlace"
    for raiz in RAICES_DE_MEDICACION:
        if raiz in t:
            return False, f"menciona medicación ({raiz})"
    permitidos = _numeros(json.dumps(contexto, ensure_ascii=False, default=str)) | _numeros(pregunta or "")
    inventados = _numeros(texto) - permitidos
    if inventados:
        return False, f"contiene números que no están en el estado: {', '.join(sorted(inventados))}"
    usados = {n for n in NIVELES if re.search(rf"\b{n}\b", t)} | {es for en, es in NIVELES_EN.items() if re.search(rf"\b{en}\b", t)}
    ajenos = usados - _niveles_permitidos(contexto)
    if ajenos:
        return False, f"menciona un nivel de alerta que no corresponde: {', '.join(sorted(ajenos))}"
    return True, "ok"


_PALABRAS_EN = {"the", "and", "you", "are", "how", "what", "is", "my", "me", "i", "feel", "feeling", "hello", "hi", "today", "am", "with", "this", "that", "not", "do", "can", "want", "need", "help", "tired", "alone", "lonely"}
_PALABRAS_ES = {"el", "la", "los", "las", "y", "que", "qué", "como", "cómo", "estoy", "me", "mi", "hola", "hoy", "con", "esto", "no", "puedo", "quiero", "necesito", "ayuda", "cansado", "solo", "sola", "siento", "estás", "esta", "está"}


def detectar_idioma(texto: str) -> str:
    """'en' si el texto parece inglés; en cualquier otro caso (o si hay duda) 'es'. Heurística simple, sin red."""
    palabras = re.findall(r"[a-záéíóúñü']+", (texto or "").lower())
    en = sum(1 for p in palabras if p in _PALABRAS_EN)
    es = sum(1 for p in palabras if p in _PALABRAS_ES)
    return "en" if en > es else "es"


# ---------- saneado de lo que entra a un prompt ----------
# Marcas con las que los modelos delimitan roles; dentro de un dato del usuario no tienen sentido y se quitan.
_MARCAS_ESPECIALES = re.compile(r"<\|[^|>]{0,40}\|>|\[/?(?:INST|SYS)\]|<<\s*/?SYS\s*>>|</?s>|```+", re.I)
_ENCABEZADO_DE_ROL = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:system|sistema|assistant|asistente|user|usuario|human|ai)\s*[:>]\s*")
_INVISIBLES = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
_INTENTOS = re.compile(
    r"(ignor[ae]\w*|olvid[ae]\w*|disregard|forget)\W+(\w+\W+){0,4}(instrucc|instruction|regla|rule|prompt)|"
    r"(revela|muestra|repite|dime|reveal|show|print|repeat)\W+(\w+\W+){0,4}(prompt|instrucc|instruction|system)|"
    r"(ahora\s+eres|you\s+are\s+now|act[uú]a\s+como|pretend\s+to\s+be)|jailbreak|\bDAN\b", re.I)


def sanear_para_prompt(texto: str, maximo: int = 500) -> str:
    """Limpia un texto del usuario antes de ponerlo en un prompt: normaliza Unicode, quita caracteres de control e
    invisibles, marcas de plantilla de chat, encabezados que imitan un rol y bloques de código, colapsa espacios y recorta.
    No cambia el sentido de una frase normal."""
    t = unicodedata.normalize("NFKC", texto or "")
    t = _INVISIBLES.sub("", t)
    t = "".join(c for c in t if c in "\n\t" or (ord(c) >= 32 and ord(c) != 127))
    t = _MARCAS_ESPECIALES.sub(" ", t)
    t = _ENCABEZADO_DE_ROL.sub("", t)
    return " ".join(t.split())[:maximo]


def parece_inyeccion(texto: str) -> bool:
    """True si el texto intenta cambiar las reglas o sacar las instrucciones. Solo sirve para registrar el intento (sin
    guardar el texto): la defensa real es el saneado, el dato entre comillas y la validación de la salida."""
    return bool(_INTENTOS.search(unicodedata.normalize("NFKC", texto or "")))


def _filtra_instrucciones(salida_normalizada: str, secretos: tuple[str, ...], ventana: int = 6) -> bool:
    """True si la salida contiene `ventana` palabras seguidas de alguno de los textos secretos (las instrucciones)."""
    pal_salida = salida_normalizada.split()
    if len(pal_salida) < ventana:
        return False
    huella = {" ".join(pal_salida[i:i + ventana]) for i in range(len(pal_salida) - ventana + 1)}
    for secreto in secretos:
        pal = normalizar(secreto).split()
        for i in range(len(pal) - ventana + 1):
            if " ".join(pal[i:i + ventana]) in huella:
                return True
    return False
