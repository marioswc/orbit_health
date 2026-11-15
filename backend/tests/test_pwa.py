import json
import re
import struct
from pathlib import Path

import pytest

from app.api.referencia import RUTAS_PUBLICAS  # noqa: F401  (comprueba que el módulo importa)

RAIZ = Path(__file__).resolve().parents[2]
PUBLIC = RAIZ / "frontend" / "public"
MANIFIESTO = json.loads((PUBLIC / "manifest.webmanifest").read_text(encoding="utf-8"))


def _dim_png(ruta: Path) -> tuple[int, int]:
    datos = ruta.read_bytes()
    assert datos[:8] == b"\x89PNG\r\n\x1a\n", f"{ruta.name} no es un PNG"
    return struct.unpack(">II", datos[16:24])


def test_el_manifiesto_cumple_lo_que_exigen_los_navegadores_para_instalar():
    m = MANIFIESTO
    for campo in ("name", "short_name", "start_url", "display", "icons", "background_color", "theme_color", "id", "scope"):
        assert m.get(campo), campo
    assert m["display"] in ("standalone", "fullscreen", "minimal-ui")
    assert m["start_url"].startswith("/") and m["scope"] == "/"
    tamanos = {(i["sizes"], i.get("purpose", "any")) for i in m["icons"]}
    assert ("192x192", "any") in tamanos and ("512x512", "any") in tamanos and ("512x512", "maskable") in tamanos


@pytest.mark.parametrize("icono", [i for i in MANIFIESTO["icons"] if i["type"] == "image/png"], ids=lambda i: i["src"])
def test_cada_icono_png_existe_y_mide_lo_que_dice(icono):
    ruta = PUBLIC / icono["src"].lstrip("/")
    assert ruta.exists(), ruta
    ancho, alto = _dim_png(ruta)
    assert f"{ancho}x{alto}" == icono["sizes"]


def test_los_atajos_de_la_app_apuntan_a_pestanas_que_existen():
    barra = (RAIZ / "frontend" / "src" / "app" / "BarraLateral.tsx").read_text(encoding="utf-8")
    ids = set(re.findall(r'id:\s*"([a-z]+)"', barra))
    assert MANIFIESTO["shortcuts"]
    for a in MANIFIESTO["shortcuts"]:
        assert re.fullmatch(r"/#/[a-z]+", a["url"]), a["url"]
        assert a["url"].split("/")[-1] in ids, a["url"]


def test_el_service_worker_nunca_guarda_la_api_y_precarga_archivos_que_existen():
    sw = (PUBLIC / "sw.js").read_text(encoding="utf-8")
    assert 'url.pathname.startsWith("/api")' in sw and "return;" in sw.split('startsWith("/api")')[1][:40]
    precarga = re.search(r"const PRECARGA = \[(.*?)\];", sw, re.S).group(1)
    for ruta in re.findall(r'"(/[^"]*)"', precarga):
        if ruta != "/":
            assert (PUBLIC / ruta.lstrip("/")).exists(), ruta
    assert "offline.html" in sw and "controllerchange" not in sw          # la recarga la decide la página, no el worker


def test_la_pagina_sin_conexion_esta_en_los_dos_idiomas_y_no_carga_nada_remoto():
    html = (PUBLIC / "offline.html").read_text(encoding="utf-8")
    assert "Retry" in html and "Reintentar" in html and "http://" not in html and "https://" not in html


def test_el_index_enlaza_manifiesto_iconos_y_color_de_tema():
    html = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    for esperado in ('rel="manifest"', 'rel="apple-touch-icon"', 'name="theme-color"', "viewport-fit=cover"):
        assert esperado in html


def test_la_pagina_y_el_service_worker_se_revalidan_y_los_assets_con_hash_se_guardan(cliente, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app import config, main
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>")
    (dist / "sw.js").write_text("//sw")
    (dist / "assets" / "app-abc123.js").write_text("const datos = '" + ("x" * 2048) + "';")
    monkeypatch.setattr(config, "FRONTEND_DIST", str(dist))
    originales = list(main.app.router.routes)
    main.app.router.routes = [r for r in originales if getattr(r, "name", "") != "frontend"]
    main._montar_frontend()
    try:
        with TestClient(main.app) as c:
            assert c.get("/sw.js").headers["cache-control"] == "no-cache"
            assert c.get("/").headers["cache-control"] == "no-cache"
            asset = c.get("/assets/app-abc123.js", headers={"Accept-Encoding": "gzip"})
            assert asset.headers["cache-control"] == "public, max-age=31536000, immutable"
            assert asset.headers["content-encoding"] == "gzip"
            assert asset.headers["vary"] == "Accept-Encoding"
            assert c.get("/api/salud").headers["cache-control"] == "no-store"
    finally:
        main.app.router.routes = originales                          # no dejar la app apuntando a una carpeta temporal
