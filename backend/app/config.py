"""Configuración del sistema, leída del entorno y de un archivo .env.

Reglas (pensadas para que un error de despliegue NUNCA pase en silencio):
- Un valor vacío cuenta como "no definido": se usa el valor por defecto.
- Se quitan espacios, comillas alrededor del valor y comentarios en la misma línea (`ORBIT_AUTH=1  # nota`). `docker run --env-file`
  deja las comillas dentro del valor; aquí se normalizan.
- Los booleanos aceptan 1/0, true/false, yes/no, on/off, si/no. Cualquier otro texto detiene el arranque con un mensaje claro:
  antes, `ORBIT_AUTH=true` dejaba la autenticación APAGADA sin avisar.
- Los números y las opciones cerradas también se validan por nombre de variable.
- Cada variable leída queda registrada con su valor y su origen (entorno, .env o por defecto), para el diagnóstico.
"""
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Variables ORBIT_* que NO lee este módulo pero sí los scripts, el lanzador o Docker: no son errores de escritura.
VARIABLES_EXTERNAS = frozenset({
    "ORBIT_HOST", "ORBIT_PUERTO", "ORBIT_PERMITIR_RED", "ORBIT_ENV_FILE", "ORBIT_TOKEN", "ORBIT_AUDITORIA_SIN_RED",
    "ORBIT_OLLAMA_DIR", "ORBIT_SIN_IA", "ORBIT_CONTENEDOR_HOST",
})
SECRETOS = frozenset({"ORBIT_DEEPSEEK_API_KEY", "ORBIT_TOKEN"})


class ErrorDeConfiguracion(ValueError):
    """Un valor de configuración no es válido. El mensaje dice qué variable y qué se esperaba."""


_LEIDAS: dict[str, dict] = {}          # nombre -> {"valor": texto crudo o None, "origen": "entorno" | ".env" | "defecto"}
_DESDE_DOTENV: set[str] = set()
_VERDADEROS = {"1", "true", "yes", "y", "on", "si", "sí", "verdadero"}
_FALSOS = {"0", "false", "no", "n", "off", "falso"}


def _limpiar(valor: str) -> str:
    """Quita espacios, un par de comillas alrededor y un comentario ` # ...` al final de un valor sin comillas."""
    v = valor.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1].strip()
    return re.split(r"\s+#", v, maxsplit=1)[0].strip()


def _crudo(nombre: str) -> str | None:
    v = os.environ.get(nombre)
    limpio = _limpiar(v) if v is not None else ""
    origen = ".env" if nombre in _DESDE_DOTENV else "entorno"
    _LEIDAS[nombre] = {"valor": limpio or None, "origen": origen if limpio else "defecto"}
    return limpio or None


def _texto(nombre: str, defecto: str = "") -> str:
    return _crudo(nombre) or defecto


def _bool(nombre: str, defecto: bool) -> bool:
    v = _crudo(nombre)
    if v is None:
        return defecto
    t = v.lower()
    if t in _VERDADEROS:
        return True
    if t in _FALSOS:
        return False
    raise ErrorDeConfiguracion(f"{nombre}={v!r} no es un valor sí/no válido. Usa 1 o 0 (también sirven true/false, yes/no, on/off).")


def _numero(nombre: str, defecto, tipo):
    v = _crudo(nombre)
    if v is None:
        return defecto
    try:
        return tipo(v)
    except ValueError:
        raise ErrorDeConfiguracion(f"{nombre}={v!r} no es un {'entero' if tipo is int else 'número'} válido.") from None


def _entero(nombre: str, defecto: int) -> int:
    return _numero(nombre, defecto, int)


def _real(nombre: str, defecto: float) -> float:
    return _numero(nombre, defecto, float)


def _opcion(nombre: str, validas: set[str], defecto: str = "") -> str:
    v = (_crudo(nombre) or defecto).lower()
    if v not in validas:
        raise ErrorDeConfiguracion(f"{nombre}={v!r} no es válido. Opciones: {', '.join(sorted(x or '(vacío)' for x in validas))}.")
    return v


def variables_leidas() -> dict[str, dict]:
    """Para el diagnóstico: cada variable que el sistema leyó, con su valor (enmascarado si es secreto) y su origen."""
    return {n: {"valor": ("***" if n in SECRETOS and d["valor"] else d["valor"]), "origen": d["origen"]} for n, d in sorted(_LEIDAS.items())}


def resolver_ruta(ruta: str) -> Path:
    """Convierte una ruta de configuración en una ruta real. Una ruta relativa (como `./models/whisper-small`) se busca, en este
    orden, junto a la base de datos (la carpeta de datos del usuario), en el directorio de trabajo, junto al ejecutable y en
    `backend/`; así funciona igual con run.sh, con el ejecutable de doble clic y en Docker. Devuelve la primera que exista, o
    la primera candidata si ninguna existe (el llamador decide qué hacer)."""
    p = Path(ruta).expanduser()
    if p.is_absolute():
        return p
    candidatas = [Path(os.environ.get("ORBIT_DB_PATH") or RAIZ / "data" / "x").parent / p, Path.cwd() / p,
                  Path(sys.executable).resolve().parent / p, RAIZ / "backend" / p, RAIZ / p]
    return next((c for c in candidatas if c.exists()), candidatas[0])


def _ruta_dotenv() -> Path | None:
    """Dónde buscar el .env. Normal: la raíz del proyecto. Ejecutable empaquetado: RAIZ sería una carpeta temporal (y su
    padre, un directorio compartido), así que NUNCA se busca ahí; solo el archivo que el lanzador indique, dentro de la
    carpeta de datos del propio usuario."""
    indicada = os.environ.get("ORBIT_ENV_FILE", "")
    if indicada:                                          # una ruta explícita manda en cualquier modo (y permite aislar pruebas)
        return Path(indicada)
    return None if getattr(sys, "frozen", False) else RAIZ / ".env"


def leer_dotenv(ruta: Path) -> dict[str, str]:
    """Interpreta un .env: `CLAVE=valor`, comentarios con #, `export CLAVE=valor`, comillas y comentario al final."""
    salida: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():      # utf-8-sig: tolera la marca BOM que añade el Bloc de notas
        texto = linea.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        if texto.startswith("export "):
            texto = texto[7:].lstrip()
        clave, valor = texto.split("=", 1)
        salida[clave.strip()] = _limpiar(valor)
    return salida


def _cargar_dotenv() -> None:
    """Carga el .env automáticamente (salvo en pytest). Lo que ya esté definido en el entorno GANA al .env."""
    if "pytest" in sys.modules:
        return
    ruta = _ruta_dotenv()
    if ruta is None or not ruta.is_file():
        return
    for k, v in leer_dotenv(ruta).items():
        if not os.environ.get(k):
            os.environ[k] = v
            _DESDE_DOTENV.add(k)


_cargar_dotenv()

# Ruta absoluta por defecto: no depende del directorio desde el que se arranque.
DB_PATH = _texto("ORBIT_DB_PATH", str(RAIZ / "data" / "orbit_health.db"))
FACTOR_ACELERACION = _real("ORBIT_FACTOR_ACELERACION", 30)
# Variación aleatoria del retardo en % (0 = determinista). La semilla hace repetible una demo con jitter.
JITTER_PCT = _real("ORBIT_JITTER_PCT", 0)
JITTER_SEMILLA = _crudo("ORBIT_JITTER_SEMILLA")
from .dominio.umbrales import UMBRALES  # noqa: E402

# Los valores por defecto salen de datos/umbrales.json; la variable de entorno tiene prioridad.
VENTANA_NEWS2_MIN = _entero("ORBIT_VENTANA_NEWS2_MIN", UMBRALES["ventana_news2_min"])
DIAS_LINEA_BASE = _entero("ORBIT_DIAS_LINEA_BASE", UMBRALES["linea_base"]["dias"])
# Endpoints de escenarios de demostración (escriben datos): desactivar fuera de la demo.
DEMO_API = _bool("ORBIT_DEMO_API", True)
SEED_DEMO = _bool("ORBIT_SEED_DEMO", True)
FRONTEND_DIST = _texto("ORBIT_FRONTEND_DIST")

# --- Seguridad a bordo (sin internet: todo local) ---
# Desactivada por defecto para la demo en una sola estación; obligatoria al exponer el servicio en red.
AUTH_ACTIVA = _bool("ORBIT_AUTH", False)
PBKDF2_ITER = _entero("ORBIT_PBKDF2_ITER", 200000)
SESION_HORAS = _real("ORBIT_SESION_HORAS", 12)
MAX_INTENTOS = _entero("ORBIT_MAX_INTENTOS", 5)
BLOQUEO_MIN = _real("ORBIT_BLOQUEO_MIN", 5)   # temporal: nunca permanente

# --- Autorrecuperación: a bordo nadie puede reparar el sistema ---
DIR_RESPALDOS = _texto("ORBIT_DIR_RESPALDOS", str(RAIZ / "data" / "respaldos"))
RESPALDO_CADA_MIN = _real("ORBIT_RESPALDO_CADA_MIN", 30)   # 0 = sin respaldos automáticos
RESPALDOS_CONSERVAR = _entero("ORBIT_RESPALDOS_CONSERVAR", 24)

# --- Flujo continuo de sensores (una banda envía una muestra por segundo): se agrupa en ventanas ---
FLUJO_VENTANA_S = _real("ORBIT_FLUJO_VENTANA_S", 60)             # 0 = sin agrupar
COMPACTAR_RUTINA_DESDE = _entero("ORBIT_COMPACTAR_RUTINA_DESDE", 20)  # eventos de rutina retenidos que disparan el resumen; 0 = nunca
FLUJO_ENFRIAMIENTO_S = _real("ORBIT_FLUJO_ENFRIAMIENTO_S", 30)   # mínimo entre extremos del mismo indicador

# Explicador opcional: solo acepta un modelo servido en la propia estación.
# Si no se configura, se usa la explicación determinista local.
IA_LOCAL_URL = _texto("ORBIT_IA_LOCAL_URL")
IA_LOCAL_MODELO = _texto("ORBIT_IA_LOCAL_MODELO")
IA_LOCAL_TIMEOUT_S = _real("ORBIT_IA_LOCAL_TIMEOUT_S", 4)

# Proveedor externo opcional (DeepSeek, API compatible con OpenAI). OJO: el texto sale del equipo.
# "automatico" prueba Ollama, luego DeepSeek si hay API key; "local" fuerza la estación.
# Vacío conserva la selección heredada: DeepSeek si hay API key, si no Ollama.
DEEPSEEK_API_KEY = _texto("ORBIT_DEEPSEEK_API_KEY")
DEEPSEEK_MODELO = _texto("ORBIT_DEEPSEEK_MODELO", "deepseek-flash")
DEEPSEEK_URL = _texto("ORBIT_DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_TIMEOUT_S = _real("ORBIT_DEEPSEEK_TIMEOUT_S", 20)
IA_PROVEEDOR = _opcion("ORBIT_IA_PROVEEDOR", {"", "local", "deepseek", "automatico", "auto"})

# Voz local opcional. Se carga solo cuando se invoca el endpoint de voz.
VOZ_ACTIVA = _bool("ORBIT_VOZ_ACTIVA", False)
VOZ_STT_MODELO = _texto("ORBIT_VOZ_STT_MODELO")
VOZ_STT_LOCAL_ONLY = _bool("ORBIT_VOZ_STT_LOCAL_ONLY", True)
VOZ_PIPER_BIN = _texto("ORBIT_VOZ_PIPER_BIN", "piper")
VOZ_PIPER_MODELO = _texto("ORBIT_VOZ_PIPER_MODELO")
VOZ_PIPER_MODELO_EN = _texto("ORBIT_VOZ_PIPER_MODELO_EN")        # voz en inglés (opcional)
VOZ_MAX_AUDIO_BYTES = _entero("ORBIT_VOZ_MAX_AUDIO_BYTES", 10000000)
VOZ_MAX_RESPUESTA_CARACTERES = _entero("ORBIT_VOZ_MAX_RESPUESTA_CARACTERES", 600)

# Rendimiento de la IA local: mantener el modelo en memoria y cargarlo (y la voz) al arrancar, para que la primera
# pregunta no pague la carga (unos 10 s en la laptop de desarrollo).
IA_LOCAL_KEEP_ALIVE = _texto("ORBIT_IA_LOCAL_KEEP_ALIVE", "30m")
PRECALENTAR = _bool("ORBIT_PRECALENTAR", True)

# Protección contra saturar el modelo local (CPU de la laptop de a bordo).
IA_MAX_SIMULTANEAS = _entero("ORBIT_IA_MAX_SIMULTANEAS", 2)
IA_PETICIONES_POR_MIN = _entero("ORBIT_IA_PETICIONES_POR_MIN", 30)        # por persona; 0 = sin límite

# IA incrustada (llama.cpp dentro del programa, sin Ollama): ruta a un .gguf; 0 hilos = todos los núcleos.
IA_MODELO_GGUF = _texto("ORBIT_IA_MODELO_GGUF")
IA_HILOS = _entero("ORBIT_IA_HILOS", 0)                       # 0 = automático: los núcleos FÍSICOS (usar los hilos lógicos sobrecarga el procesador)
IA_EMBEBIDA_TIMEOUT_S = _real("ORBIT_IA_EMBEBIDA_TIMEOUT_S", 60)   # tiempo máximo generando una respuesta con el modelo incrustado
IA_DESCARGA_MIN = _real("ORBIT_IA_DESCARGA_MIN", 15)               # minutos sin usar el modelo incrustado antes de liberar su memoria (0 = nunca)
PRECALENTAR_VOZ = _bool("ORBIT_PRECALENTAR_VOZ", False)            # cargar también el reconocimiento de voz al arrancar (ocupa memoria)
