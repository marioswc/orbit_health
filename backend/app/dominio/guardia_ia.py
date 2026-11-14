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
)


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


def validar_respuesta(texto: str | None, contexto, pregunta: str = "") -> tuple[bool, str]:
    """(ok, motivo). `contexto` es el estado ya calculado; `pregunta` es lo que dijo el usuario (si lo hubo)."""
    if not texto or not texto.strip():
        return False, "respuesta vacía"
    if len(texto) > MAX_CARACTERES:
        return False, "respuesta demasiado larga"
    t = normalizar(texto)
    if "http://" in t or "https://" in t or "www." in t:
        return False, "contiene un enlace"
    for raiz in RAICES_DE_MEDICACION:
        if raiz in t:
            return False, f"menciona medicación ({raiz})"
    permitidos = _numeros(json.dumps(contexto, ensure_ascii=False, default=str)) | _numeros(pregunta or "")
    inventados = _numeros(texto) - permitidos
    if inventados:
        return False, f"contiene números que no están en el estado: {', '.join(sorted(inventados))}"
    usados = {n for n in NIVELES if re.search(rf"\b{n}\b", t)}
    ajenos = usados - _niveles_permitidos(contexto)
    if ajenos:
        return False, f"menciona un nivel de alerta que no corresponde: {', '.join(sorted(ajenos))}"
    return True, "ok"
