#!/usr/bin/env python3
"""Mide los tiempos de respuesta reales del servidor por HTTP en este equipo, con una base temporal.

Uso: backend/.venv/bin/python scripts/medir_tiempos.py [repeticiones]
Arranca el servidor, lanza las peticiones, imprime percentiles y lo detiene. No toca la base real.
"""
import http.client
import json
import os
import platform
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def pedir(conn: http.client.HTTPConnection, metodo: str, ruta: str, cuerpo: dict | None = None) -> float:
    datos = json.dumps(cuerpo) if cuerpo else None
    t0 = time.perf_counter()
    conn.request(metodo, ruta, body=datos, headers={"Content-Type": "application/json"} if datos else {})
    r = conn.getresponse()
    r.read()
    dt = (time.perf_counter() - t0) * 1000
    if r.status != 200:
        raise SystemExit(f"{metodo} {ruta} devolvió {r.status}")
    return dt


def resumen(nombre: str, ms: list[float]) -> dict:
    ms = sorted(ms)
    p = lambda q: ms[min(len(ms) - 1, int(len(ms) * q))]
    return {"operacion": nombre, "n": len(ms), "p50_ms": round(p(0.50), 2), "p95_ms": round(p(0.95), 2),
            "max_ms": round(ms[-1], 2), "media_ms": round(statistics.fmean(ms), 2)}


def main() -> int:
    tmp = tempfile.mkdtemp()
    puerto = puerto_libre()
    env = {**os.environ, "ORBIT_DB_PATH": f"{tmp}/m.db", "ORBIT_DIR_RESPALDOS": f"{tmp}/r",
           "ORBIT_RESPALDO_CADA_MIN": "0", "ORBIT_AUTH": "0", "ORBIT_SEED_DEMO": "1"}
    uv = RAIZ / "backend" / ".venv" / "bin" / "uvicorn"
    srv = subprocess.Popen([str(uv), "app.main:app", "--host", "127.0.0.1", "--port", str(puerto), "--log-level", "warning"],
                           cwd=RAIZ / "backend", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", puerto, timeout=10)
        for _ in range(60):
            try:
                pedir(conn, "GET", "/api/health"); break
            except (ConnectionRefusedError, OSError):
                conn = http.client.HTTPConnection("127.0.0.1", puerto, timeout=10); time.sleep(0.2)
        else:
            raise SystemExit("El servidor no arrancó")
        for _ in range(20):                                     # calentamiento: no cuenta
            pedir(conn, "POST", "/api/lecturas", {"tripulante_id": "T1", "indicador": "spo2", "valor": 97})
        valores = [97, 96, 98, 95, 88, 99]
        t_post = [pedir(conn, "POST", "/api/lecturas", {"tripulante_id": "T1", "indicador": "spo2", "valor": valores[i % 6]}) for i in range(N)]
        t_estado = [pedir(conn, "GET", "/api/estado/T1") for _ in range(N)]
        t_hist = [pedir(conn, "GET", "/api/historial/T1?indicador=spo2") for _ in range(N)]
        t_inf = [pedir(conn, "GET", "/api/informe/T1") for _ in range(N)]
    finally:
        srv.terminate(); srv.wait(timeout=10)
    salida = {
        "equipo": {"so": platform.platform(), "python": platform.python_version(), "cpus": os.cpu_count()},
        "nota": "HTTP por localhost con una base SQLite temporal; sin red real, sin autenticación, sin carga concurrente.",
        "resultados": [resumen("POST /api/lecturas (clasifica, guarda y encola)", t_post),
                       resumen("GET /api/estado/{id}", t_estado),
                       resumen("GET /api/historial/{id}", t_hist),
                       resumen("GET /api/informe/{id}", t_inf)],
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
