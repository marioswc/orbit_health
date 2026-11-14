import json

import pytest

from app.dominio import explicaciones as e
from app.dominio.catalogos import INDICADORES

PROHIBIDAS = ("administra", "dosis de", "medicamento", "toma ", "inyec", "tratamiento con", "receta", "fármaco", "farmaco")


def test_hay_explicacion_para_cada_indicador_y_el_animo():
    assert (set(INDICADORES) | {"animo"}) <= set(e.DATOS["explicaciones"])


def test_cada_explicacion_esta_completa_y_con_fuentes_https():
    for clave, x in e.DATOS["explicaciones"].items():
        assert all(x[c] for c in e.CAMPOS), clave
        assert all(u.startswith("https://") for u in x["fuentes"]), clave


def test_las_explicaciones_no_dan_consejo_medico_ni_de_medicacion():
    texto = json.dumps(e.DATOS, ensure_ascii=False).lower()
    for palabra in PROHIBIDAS:
        assert palabra not in texto, palabra


def test_se_declara_pendiente_de_validacion_y_que_no_sustituye_al_medico():
    assert e.DATOS["estado"].startswith("pendiente") and "no sustituye" in e.DATOS["aviso"].lower()


def test_el_animo_se_declara_privado():
    assert "privado" in e.DATOS["explicaciones"]["animo"]["cuando_avisar"].lower()


def test_las_fuentes_de_cada_explicacion_son_de_las_paginas_oficiales_conocidas():
    from app.dominio import peligros
    conocidas = {r["url"] for r in peligros.DATOS["riesgos"]} | {p["url"] for p in peligros.DATOS["peligros"].values()}
    conocidas |= {"https://www.nasa.gov/reference/archer",
                  "https://www.canada.ca/en/space-agency/news/2026/02/canadian-space-radiation-technology-to-support-health-and-safety.html"}
    for clave, x in e.DATOS["explicaciones"].items():
        assert set(x["fuentes"]) <= conocidas, clave


def test_rechaza_explicacion_incompleta(tmp_path):
    malo = tmp_path / "x.json"
    malo.write_text(json.dumps({"explicaciones": {"x": {"que_es": "a"}}}))
    with pytest.raises(e.ExplicacionesInvalidas):
        e.cargar(malo)


def test_endpoints_publicos(cliente):
    todas = cliente.get("/api/explicaciones").json()
    assert "spo2" in todas["explicaciones"]
    una = cliente.get("/api/explicaciones/spo2").json()
    assert una["clave"] == "spo2" and una["fuentes"] and "oxígeno" in una["que_es"].lower()
    assert cliente.get("/api/explicaciones/nada").status_code == 404


def test_son_publicas_aun_con_autenticacion(cliente_auth):
    assert cliente_auth.get("/api/explicaciones/co2").status_code == 200       # contenido educativo, sin datos de salud
