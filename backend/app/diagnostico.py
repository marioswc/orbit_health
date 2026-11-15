"""`python -m app.diagnostico [--json]`: muestra la configuración efectiva y los problemas de despliegue."""
import json
import sys

from .servicios import diagnostico


def main(argv: list[str]) -> int:
    d = diagnostico.reunir()
    if "--advertencias" in argv:                    # lo usa el contenedor al arrancar: solo lo que merece atención, en pocas líneas
        for a in d["advertencias"]:
            print(f"[ORBIT {a['nivel'].upper()}] {a['tema']}: {a['detalle']}" + (f" -> {a['arreglo']}" if a.get("arreglo") else ""))
        return 1 if any(a["nivel"] == "error" for a in d["advertencias"]) else 0
    print(json.dumps(d, indent=2, ensure_ascii=False) if "--json" in argv else diagnostico.como_texto(d))
    return 1 if any(a["nivel"] == "error" for a in d["advertencias"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
