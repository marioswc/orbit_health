import json
from pathlib import Path

import pytest

from app.dominio import peligros as p

OFICIALES_17 = 17
PELIGROS_5 = {"radiacion", "aislamiento_confinamiento", "distancia_tierra", "campos_gravedad", "entornos_hostiles_cerrados"}


def test_estan_los_5_peligros_y_los_17_riesgos_oficiales():
    assert set(p.DATOS["peligros"]) == PELIGROS_5
    assert len(p.DATOS["riesgos"]) == OFICIALES_17
    assert len({r["nombre_oficial"] for r in p.DATOS["riesgos"]}) == OFICIALES_17


def test_todo_enlace_es_oficial_de_nasa():
    urls = [r["url"] for r in p.DATOS["riesgos"]] + [x["url"] for x in p.DATOS["peligros"].values()]
    assert all(u.startswith("https://www.nasa.gov/") for u in urls)


def test_la_cobertura_declarada_es_honesta_y_coherente():
    for r in p.DATOS["riesgos"]:
        if r["cobertura"] == "no_cubierto":
            assert r["indicadores"] == [], r["nombre_oficial"]
        else:
            assert r["indicadores"], r["nombre_oficial"]
            assert set(r["indicadores"]) <= p.indicadores_conocidos(), r["nombre_oficial"]
    resumen = p.resumen_cobertura()
    assert resumen["total"] == 17 and resumen["cubierto"] + resumen["parcial"] + resumen["no_cubierto"] == 17
    assert resumen["no_cubierto"] > resumen["cubierto"]            # no inflamos lo que cubrimos


def test_cada_indicador_conocido_tiene_asociacion_declarada():
    assert p.indicadores_conocidos() <= set(p.DATOS["indicadores_por_peligro"])


def test_se_declara_que_la_asociacion_no_es_oficial():
    assert "no clasifica" in p.DATOS["estado"]


def test_peligros_de_indicadores_sin_repetir():
    r = p.peligros_de(["spo2", "co2", "dosis_pct"])
    assert [x["id"] for x in r] == ["entornos_hostiles_cerrados", "radiacion"]
    assert p.peligros_de(["avpu"]) == []


def test_rechaza_cobertura_sin_indicadores_y_urls_no_oficiales(tmp_path):
    d = json.loads(Path(p.RUTA).read_text(encoding="utf-8"))
    d["riesgos"][0]["indicadores"] = []
    f = tmp_path / "x.json"; f.write_text(json.dumps(d))
    with pytest.raises(p.PeligrosInvalidos):
        p.cargar(f)
    d = json.loads(Path(p.RUTA).read_text(encoding="utf-8"))
    d["riesgos"][0]["url"] = "https://ejemplo.com/x"
    f.write_text(json.dumps(d))
    with pytest.raises(p.PeligrosInvalidos):
        p.cargar(f)


def test_endpoint_publico_con_resumen(cliente):
    r = cliente.get("/api/peligros").json()
    assert r["resumen_cobertura"]["total"] == 17 and len(r["peligros"]) == 5


def test_las_alertas_se_ligan_a_su_peligro(cliente):
    r = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88}).json()
    assert r["peligros_relacionados"][0]["id"] == "entornos_hostiles_cerrados"
    verde = cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "spo2", "valor": 98}).json()
    assert verde["peligros_relacionados"] == []
    e = cliente.get("/api/estado/T1").json()
    assert [x["id"] for x in e["peligros_relacionados"]] == ["entornos_hostiles_cerrados"]
    cliente.post("/api/lecturas", json={"tripulante_id": "T3", "indicador": "sueno_horas", "valor": 3})
    assert cliente.get("/api/estado/T3").json()["peligros_relacionados"][0]["id"] == "aislamiento_confinamiento"


def test_endpoint_publico_con_autenticacion(cliente_auth):
    assert cliente_auth.get("/api/peligros").status_code == 200
