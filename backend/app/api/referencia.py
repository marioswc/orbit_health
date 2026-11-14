"""Referencia de la API generada desde el propio código (OpenAPI), para que la documentación no pueda desfasarse.

`RUTAS_PUBLICAS` es el contrato de seguridad: son las únicas rutas que responden sin sesión cuando la autenticación
está activa. Una prueba recorre todas las rutas y falla si alguna otra queda abierta.
"""
from __future__ import annotations

# (método, ruta) que NO exigen sesión. Cada una tiene una razón:
RUTAS_PUBLICAS = {
    ("GET", "/api/health"),                      # comprobación de que el servidor vive
    ("GET", "/api/salud"),                       # estado de la base y de los respaldos para un tripulante no técnico
    ("GET", "/api/auth/estado"),                 # la interfaz necesita saber si debe mostrar el acceso
    ("POST", "/api/auth/login"),                 # iniciar sesión
    ("POST", "/api/auth/recuperar"),             # recuperar el PIN con el código de recuperación
    ("GET", "/api/tripulantes"),                 # el selector de acceso necesita los nombres (solo id, nombre y rol)
    ("GET", "/api/indicadores"),                 # catálogo, sin datos de salud
    ("GET", "/api/umbrales"),                    # versión y estado de validación de los umbrales
    ("GET", "/api/explicaciones"),               # contenido educativo, sin datos de salud
    ("GET", "/api/explicaciones/{clave}"),
    ("GET", "/api/peligros"),                    # marco de peligros y riesgos del HRP, sin datos de salud
}

ENCABEZADO = """# Referencia de la API

> **Generado automáticamente** por `scripts/generar_api_doc.py` a partir del código. No se edita a mano: una prueba
> falla si este archivo no coincide con las rutas reales. Para regenerarlo: `backend/.venv/bin/python scripts/generar_api_doc.py`.

Con `ORBIT_AUTH=1` todas las rutas exigen sesión (`Authorization: Bearer <token>`) **excepto** las marcadas como públicas.
Qué rol puede usar cada una está en [SEGURIDAD_A_BORDO.md](SEGURIDAD_A_BORDO.md).
"""

ORDEN_ETIQUETAS = ["sistema", "seguridad", "lecturas", "bienestar", "enlace", "informe", "sensores", "demo"]


def _primera_linea(op: dict) -> str:
    texto = (op.get("description") or op.get("summary") or "").strip().splitlines()
    return texto[0].strip().rstrip(".") if texto else ""


def generar_markdown(app) -> str:
    grupos: dict[str, list[tuple[str, str, str]]] = {}
    for ruta, ops in app.openapi()["paths"].items():
        if not ruta.startswith("/api"):
            continue
        for metodo, op in ops.items():
            etiqueta = (op.get("tags") or ["otros"])[0]
            grupos.setdefault(etiqueta, []).append((ruta, metodo.upper(), _primera_linea(op)))
    lineas = [ENCABEZADO]
    claves = sorted(grupos, key=lambda t: (ORDEN_ETIQUETAS.index(t) if t in ORDEN_ETIQUETAS else 99, t))
    for etiqueta in claves:
        lineas.append(f"\n## {etiqueta}\n\n| Método | Ruta | Sesión | Qué hace |\n|---|---|---|---|")
        for ruta, metodo, desc in sorted(grupos[etiqueta]):
            sesion = "pública" if (metodo, ruta) in RUTAS_PUBLICAS else "requerida"
            lineas.append(f"| {metodo} | `{ruta}` | {sesion} | {desc.replace('|', '/')} |")
    total = sum(len(v) for v in grupos.values())
    lineas.append(f"\nTotal: {total} operaciones, {len(RUTAS_PUBLICAS)} públicas.\n")
    return "\n".join(lineas)
