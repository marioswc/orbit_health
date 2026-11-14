"""Adaptadores opcionales de voz local.

El audio se procesa en memoria/archivos temporales y nunca se persiste en la
base ni se envía fuera de la estación. La voz solo produce una respuesta
conversacional; el estado clínico sigue siendo responsabilidad del motor
determinista.
"""
from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from .. import config
from . import explicador_local


class VozNoDisponible(RuntimeError):
    """La capacidad de voz no está instalada o configurada."""


@lru_cache(maxsize=1)
def _modelo_stt():
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise VozNoDisponible("Instala backend/requirements-voice.txt para activar voz") from error
    return WhisperModel(config.VOZ_STT_MODELO, device="cpu", compute_type="int8")


def transcribir(audio: bytes, extension: str = ".wav") -> str:
    if not config.VOZ_ACTIVA:
        raise VozNoDisponible("La voz local está desactivada")
    if not audio or len(audio) > config.VOZ_MAX_AUDIO_BYTES:
        raise ValueError("Audio vacío o demasiado grande")
    suffix = extension if extension in {".wav", ".webm", ".ogg", ".mp3", ".m4a"} else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as archivo:
        archivo.write(audio)
        ruta = archivo.name
    try:
        segmentos, _ = _modelo_stt().transcribe(ruta, language="es", vad_filter=True)
        texto = " ".join(s.text.strip() for s in segmentos if s.text.strip()).strip()
        if not texto:
            raise ValueError("No se pudo reconocer voz")
        return texto[:2000]
    finally:
        Path(ruta).unlink(missing_ok=True)


def responder(texto: str, estado: dict, preferencias: dict) -> dict:
    """Responde usando el LLM local, sin permitirle producir decisiones clínicas."""
    prompt = (
        "Responde en español a un astronauta en una conversación de voz breve. "
        "Usa solo sus preferencias explícitas y el estado clínico proporcionado. "
        "No diagnostiques, no prescribas tratamientos o medicamentos, no leas ni "
        "infieras datos del diario o del ánimo, y no cambies el nivel de alerta, "
        "prioridad o acciones del estado. Si pregunta por una alerta, explica que "
        "las acciones procedimentales del sistema tienen prioridad. Máximo 120 palabras.\n"
        f"Preferencias: {preferencias}\nEstado: {estado}\nPregunta: {texto}"
    )
    respuesta = explicador_local.consultar_modelo(prompt)
    if respuesta is None:
        return {
            "fuente": "reglas_locales",
            "texto": f"Recibí: «{texto}». El nivel actual es {estado.get('nivel_general', 'verde')}. "
                      "Puedo explicar el resultado, pero el modelo de conversación local no está disponible.",
        }
    return {"fuente": "modelo_local", "texto": respuesta}


def sintetizar(texto: str) -> str:
    """Devuelve audio WAV codificado, sin guardar el resultado permanentemente."""
    if not config.VOZ_PIPER_MODELO:
        raise VozNoDisponible("Configura ORBIT_VOZ_PIPER_MODELO")
    with tempfile.TemporaryDirectory() as directorio:
        salida = os.path.join(directorio, "respuesta.wav")
        try:
            subprocess.run(
                [config.VOZ_PIPER_BIN, "--model", config.VOZ_PIPER_MODELO, "--output_file", salida],
                input=texto, text=True, capture_output=True, check=True, timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise VozNoDisponible("Piper no pudo sintetizar la respuesta") from error
        return base64.b64encode(Path(salida).read_bytes()).decode("ascii")
