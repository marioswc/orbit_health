import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Ruta absoluta por defecto: no depende del directorio desde el que se arranque.
DB_PATH = os.getenv("ORBIT_DB_PATH") or str(RAIZ / "data" / "orbit_health.db")
FACTOR_ACELERACION = float(os.getenv("ORBIT_FACTOR_ACELERACION", "30"))
# Variación aleatoria del retardo en % (0 = determinista). La semilla hace repetible una demo con jitter.
JITTER_PCT = float(os.getenv("ORBIT_JITTER_PCT", "0"))
JITTER_SEMILLA = os.getenv("ORBIT_JITTER_SEMILLA")
from .dominio.umbrales import UMBRALES  # noqa: E402

# Los valores por defecto salen de datos/umbrales.json; la variable de entorno tiene prioridad.
VENTANA_NEWS2_MIN = int(os.getenv("ORBIT_VENTANA_NEWS2_MIN") or UMBRALES["ventana_news2_min"])
DIAS_LINEA_BASE = int(os.getenv("ORBIT_DIAS_LINEA_BASE") or UMBRALES["linea_base"]["dias"])
# Endpoints de escenarios de demostración (escriben datos): desactivar fuera de la demo.
DEMO_API = os.getenv("ORBIT_DEMO_API", "1") == "1"
SEED_DEMO = os.getenv("ORBIT_SEED_DEMO", "1") == "1"
FRONTEND_DIST = os.getenv("ORBIT_FRONTEND_DIST", "")

# --- Seguridad a bordo (sin internet: todo local) ---
# Desactivada por defecto para la demo en una sola estación; obligatoria al exponer el servicio en red.
AUTH_ACTIVA = os.getenv("ORBIT_AUTH", "0") == "1"
PBKDF2_ITER = int(os.getenv("ORBIT_PBKDF2_ITER", "200000"))
SESION_HORAS = float(os.getenv("ORBIT_SESION_HORAS", "12"))
MAX_INTENTOS = int(os.getenv("ORBIT_MAX_INTENTOS", "5"))
BLOQUEO_MIN = float(os.getenv("ORBIT_BLOQUEO_MIN", "5"))   # temporal: nunca permanente

# --- Autorrecuperación: a bordo nadie puede reparar el sistema ---
DIR_RESPALDOS = os.getenv("ORBIT_DIR_RESPALDOS") or str(RAIZ / "data" / "respaldos")
RESPALDO_CADA_MIN = float(os.getenv("ORBIT_RESPALDO_CADA_MIN", "30"))   # 0 = sin respaldos automáticos
RESPALDOS_CONSERVAR = int(os.getenv("ORBIT_RESPALDOS_CONSERVAR", "24"))
