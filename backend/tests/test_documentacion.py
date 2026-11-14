"""La documentación debe decir la verdad: estas pruebas cruzan los documentos con el código real."""
import re
from pathlib import Path

import pytest

from app import main
from app.api.referencia import RUTAS_PUBLICAS, generar_markdown
from app.dominio import peligros

RAIZ = Path(__file__).resolve().parents[2]
DOCS_PROPIOS = [RAIZ / "README.md", RAIZ / "README.en.md", *sorted((RAIZ / "docs").glob("*.md")),
                *sorted((RAIZ / "backend" / "docs").glob("*.md"))]
DOCS_TODOS = DOCS_PROPIOS + sorted((RAIZ / "frontend" / "docs").glob("*.md"))


def _operaciones():
    for ruta, ops in main.app.openapi()["paths"].items():
        if ruta.startswith("/api"):
            for metodo in ops:
                yield metodo.upper(), ruta


def _url(ruta):
    return re.sub(r"\{[^}]+\}", "1" if "aviso_id" in ruta else "T1", ruta)


def test_solo_las_rutas_declaradas_como_publicas_responden_sin_sesion(cliente_auth):
    """Recorre TODAS las rutas con la autenticación activa y sin token: si una nueva queda abierta, falla."""
    abiertas, cerradas_de_mas = set(), set()
    for metodo, ruta in _operaciones():
        r = cliente_auth.request(metodo, _url(ruta), json={} if metodo in ("POST", "PUT") else None)
        if r.status_code != 401:
            abiertas.add((metodo, ruta))
    assert abiertas == RUTAS_PUBLICAS, {"abiertas sin declarar": abiertas - RUTAS_PUBLICAS,
                                        "declaradas públicas pero piden sesión": RUTAS_PUBLICAS - abiertas}


def test_las_rutas_publicas_existen_realmente():
    assert RUTAS_PUBLICAS <= set(_operaciones())


def test_la_referencia_de_la_api_esta_al_dia():
    esperado = generar_markdown(main.app)
    real = (RAIZ / "docs" / "API_REFERENCIA.md").read_text(encoding="utf-8")
    assert real == esperado, "docs/API_REFERENCIA.md está desfasado: ejecuta scripts/generar_api_doc.py"


def test_toda_ruta_tiene_una_descripcion_real_y_no_solo_el_nombre_de_la_funcion():
    sin_descripcion = [(m, r) for r, ops in main.app.openapi()["paths"].items() if r.startswith("/api")
                       for m, op in ops.items() if not op.get("description")]
    assert sin_descripcion == []


def test_las_rutas_citadas_en_los_documentos_existen():
    reales = {r for _, r in _operaciones()}
    patrones = [re.compile("^" + re.sub(r"\\\{[^}]*\\\}", "[^/]+", re.escape(r)) + "$") for r in reales]
    inexistentes = []
    for doc in DOCS_PROPIOS:
        for m in re.finditer(r"(/api/[A-Za-z0-9_/{}\-]+)", doc.read_text(encoding="utf-8")):
            ruta = re.sub(r"\{[^}]*\}", "x", m.group(1)).rstrip("/")
            if not any(p.match(ruta) for p in patrones):
                inexistentes.append((doc.name, m.group(1)))
    assert inexistentes == []


@pytest.mark.parametrize("doc", DOCS_TODOS, ids=lambda p: str(p.relative_to(RAIZ)))
def test_los_enlaces_locales_de_la_documentacion_existen(doc):
    rotos = []
    for m in re.finditer(r"\]\((?!https?:|#|mailto:)([^)\s#]+)", doc.read_text(encoding="utf-8")):
        if not (doc.parent / m.group(1)).resolve().exists():
            rotos.append(m.group(1))
    assert rotos == []


def test_toda_variable_de_entorno_del_codigo_esta_en_env_example():
    codigo = "".join(p.read_text(encoding="utf-8") for p in (RAIZ / "backend" / "app").rglob("*.py"))
    codigo += (RAIZ / "run.sh").read_text(encoding="utf-8")
    usadas = set(re.findall(r"ORBIT_[A-Z0-9_]+", codigo))
    declaradas = set(re.findall(r"^#?\s*(ORBIT_[A-Z0-9_]+)=", (RAIZ / ".env.example").read_text(encoding="utf-8"), re.M))
    assert usadas - declaradas == set(), "variables que el código lee y .env.example no documenta"


def test_la_cobertura_del_hrp_que_dicen_los_documentos_es_la_real():
    r = peligros.resumen_cobertura()
    c, p, n = r["cubierto"], r["parcial"], r["no_cubierto"]
    resumen = (RAIZ / "docs" / "PROJECT_SUMMARY_EN.md").read_text(encoding="utf-8")
    assert f"{c} risk fully covered, {p} partially, {n} not covered" in resumen
    assert f"Only {c + p} of the 17 HRP risks have any indicator" in resumen
    assert f"{c} of 17 risks fully, {p} partly, {n} not covered" in (RAIZ / "README.en.md").read_text(encoding="utf-8")
    assert f"{c} de 17 riesgos cubierto, {p} parciales, {n} no" in (RAIZ / "docs" / "DECISIONES_EQUIPO.md").read_text(encoding="utf-8")


def test_los_documentos_no_citan_nombres_de_modulos_que_ya_no_existen():
    viejos = ("engine.py", "queue_manager.py", "servicio.py", "cola_tierra", "hash_ancla", "schema.sql de db.py")
    for doc in DOCS_PROPIOS:
        texto = doc.read_text(encoding="utf-8")
        for v in viejos:
            assert v not in texto, f"{doc.name} cita '{v}', que ya no existe"
