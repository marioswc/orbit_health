#!/usr/bin/env python3
"""Pone o cambia UNA variable en el .env sin tocar el resto, con permisos 600. Uso: poner_env.py CLAVE VALOR [ruta]
El valor se lee del argumento o, si es '-', de la entrada estándar (así una clave no queda en el historial del terminal).
Nunca imprime el valor."""
import os
import re
import sys
from pathlib import Path

VALIDA = re.compile(r"^ORBIT_[A-Z0-9_]+$")


def poner(ruta: Path, clave: str, valor: str) -> None:
    if not VALIDA.match(clave):
        raise ValueError(f"Nombre de variable no permitido: {clave}")
    if "\n" in valor or "\r" in valor or "\x00" in valor:
        raise ValueError("El valor no puede tener saltos de línea")
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    nueva = f"{clave}={valor}"
    patron = re.compile(rf"^\s*#?\s*{re.escape(clave)}=")
    hecho = False
    for i, linea in enumerate(lineas):
        if patron.match(linea) and not hecho:
            lineas[i] = nueva
            hecho = True
    if not hecho:
        lineas.append(nueva)
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    os.chmod(ruta, 0o600)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    clave, valor = argv[0], argv[1]
    ruta = Path(argv[2]) if len(argv) > 2 else Path(__file__).resolve().parents[1] / ".env"
    if valor == "-":
        valor = sys.stdin.readline().rstrip("\n")
    try:
        poner(ruta, clave, valor)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    print(f"{clave} actualizado en {ruta.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
