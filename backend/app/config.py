import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# Ruta absoluta por defecto: no depende del directorio desde el que se arranque.
DB_PATH = os.getenv("ORBIT_DB_PATH") or str(RAIZ / "data" / "orbit_health.db")
FACTOR_ACELERACION = float(os.getenv("ORBIT_FACTOR_ACELERACION", "30"))
LATENCIA_MARTE_S = float(os.getenv("ORBIT_LATENCIA_MARTE_S", "1200"))
LATENCIA_LUNA_S = float(os.getenv("ORBIT_LATENCIA_LUNA_S", "1.3"))
from .dominio.umbrales import UMBRALES  # noqa: E402

# Los valores por defecto salen de datos/umbrales.json; la variable de entorno tiene prioridad.
VENTANA_NEWS2_MIN = int(os.getenv("ORBIT_VENTANA_NEWS2_MIN") or UMBRALES["ventana_news2_min"])
DIAS_LINEA_BASE = int(os.getenv("ORBIT_DIAS_LINEA_BASE") or UMBRALES["linea_base"]["dias"])
SEED_DEMO = os.getenv("ORBIT_SEED_DEMO", "1") == "1"
FRONTEND_DIST = os.getenv("ORBIT_FRONTEND_DIST", "")
