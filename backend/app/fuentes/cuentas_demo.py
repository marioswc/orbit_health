"""Cuentas de DEMOSTRACIÓN con PIN fácil de recordar. Solo para ensayos y presentaciones: nunca en una misión real.

Uso: scripts/cuentas_demo.sh   (requiere ORBIT_DEMO_API=1; no toca cuentas que ya existan)
"""
import sys

from .. import config
from ..repositorios.conexion import get_conn, init_db
from ..servicios import auth
from . import semilla

CUENTAS = (("T1", "comandante", "111111"), ("T2", "tripulante", "222222"),
           ("T3", "tripulante", "333333"), ("T4", "tripulante", "444444"))


def crear(conn) -> list[tuple[str, str, str, bool]]:
    """Devuelve (id, rol, pin, creada). Si el tripulante ya tiene credenciales, no se cambia nada.
    Si la base está vacía, primero se crea la tripulación de ejemplo (T1 a T4)."""
    semilla.sembrar(conn)
    salida = []
    for tid, rol, pin in CUENTAS:
        try:
            auth.inscribir(conn, tid, rol, pin)
            salida.append((tid, rol, pin, True))
        except ValueError as e:
            if "ya tiene credenciales" not in str(e):
                raise                                       # cualquier otro motivo es un error real, no "ya existía"
            salida.append((tid, rol, pin, False))
    return salida


def main() -> int:
    if not config.DEMO_API:
        print("Las cuentas de demostración requieren ORBIT_DEMO_API=1 (son solo para ensayos).")
        return 1
    init_db()
    conn = get_conn()
    try:
        for tid, rol, pin, creada in crear(conn):
            print(f"{tid:3} {rol:11} PIN {pin}  {'creada' if creada else 'ya existía: sin cambios'}")
    finally:
        conn.close()
    print("Cuentas DEMO con PIN fácil: no usar en una misión real. Se activan con ORBIT_AUTH=1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
