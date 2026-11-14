"""Alta de credenciales desde la terminal. Los PIN no se escriben en el código ni en el repositorio.

Uso: python -m app.fuentes.inscripcion T1 comandante [PIN]
Sin PIN se genera uno aleatorio. El PIN y el código de recuperación se muestran UNA sola vez.
"""
import sys

from ..repositorios.conexion import get_conn, init_db
from ..servicios import auth


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    tid, rol = argv[0], argv[1]
    pin = argv[2] if len(argv) > 2 else None
    init_db()
    conn = get_conn()
    try:
        r = auth.inscribir(conn, tid, rol, pin)
    except ValueError as e:
        print(f"No se pudo inscribir: {e}")
        return 1
    finally:
        conn.close()
    print(f"Tripulante {r['tripulante_id']} ({r['rol']})")
    if "pin" in r:
        print(f"  PIN inicial:             {r['pin']}")
    print(f"  Código de recuperación:  {r['codigo_recuperacion']}")
    print("Anótalos ahora en un lugar seguro: no se vuelven a mostrar.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
