import os

DB_PATH = os.getenv("ORBIT_DB_PATH", "./data/orbit_health.db")
FACTOR_ACELERACION = float(os.getenv("ORBIT_FACTOR_ACELERACION", "30"))
LATENCIA_MARTE_S = float(os.getenv("ORBIT_LATENCIA_MARTE_S", "1200"))
LATENCIA_LUNA_S = float(os.getenv("ORBIT_LATENCIA_LUNA_S", "1.3"))
