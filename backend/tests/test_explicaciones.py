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


def _items(campo):
    return [(clave, it) for clave, x in e.DATOS["explicaciones"].items() for it in x.get(campo, [])]


def test_toda_medida_de_la_nasa_trae_cita_textual_y_enlace_oficial_conocido():
    from app.dominio import peligros
    oficiales = {r["url"] for r in peligros.DATOS["riesgos"]}
    for campo in ("medidas_nasa", "senales_a_vigilar"):
        elementos = _items(campo)
        assert elementos, campo
        for clave, it in elementos:
            assert it["fuente"] in oficiales, (clave, it["fuente"])
            assert len(it["cita"]) > 20, (clave, it["cita"])
            assert not it["cita"].startswith(("El ", "La ", "Los ", "Las ")), "la cita debe ir en el idioma original (inglés)"


def test_los_habitos_que_no_son_de_la_nasa_lo_declaran():
    for clave, x in e.DATOS["explicaciones"].items():
        if x.get("habitos_generales"):
            assert "no es una recomendación de la NASA" in x["habitos_generales_origen"], clave
    assert "no se atribuyen a la NASA" in e.DATOS["nota_medidas"]


def test_donde_la_nasa_no_da_guia_se_dice_y_no_se_inventa():
    g = e.DATOS["explicaciones"]["glucosa"]
    assert "no da recomendaciones sobre glucosa" in g["nota_nasa"] and not g.get("medidas_nasa")
    for clave in ("co2", "dosis_pct", "avpu"):                          # tampoco se inventan medidas donde no las leí
        assert not e.DATOS["explicaciones"][clave].get("medidas_nasa"), clave


def test_hipoxia_solo_ofrece_senales_a_vigilar_porque_la_pagina_no_describe_medidas():
    for clave in ("spo2", "frecuencia_respiratoria"):
        x = e.DATOS["explicaciones"][clave]
        assert x.get("senales_a_vigilar") and not x.get("medidas_nasa")


def test_el_ejercicio_cita_las_cifras_exactas_de_la_pagina():
    x = e.DATOS["explicaciones"]["ejercicio_min"]["medidas_nasa"][0]
    assert "6 a 7 días" in x["texto"] and "1.5 horas" in x["texto"] and "1.5 hours per day" in x["cita"]


def test_las_medidas_nasa_pasan_por_la_api(cliente):
    r = cliente.get("/api/explicaciones/sueno_horas").json()
    assert len(r["medidas_nasa"]) == 2 and r["habitos_generales_origen"]
    assert cliente.get("/api/explicaciones/glucosa").json()["nota_nasa"]


def test_se_rechaza_una_medida_sin_cita_o_con_fuente_ajena(tmp_path):
    base = json.loads(json.dumps(e.DATOS))
    base["explicaciones"]["spo2"]["senales_a_vigilar"] = [{"texto": "x", "cita": "", "fuente": "https://www.nasa.gov/a"}]
    f = tmp_path / "x.json"; f.write_text(json.dumps(base))
    with pytest.raises(e.ExplicacionesInvalidas):
        e.cargar(f)
    base = json.loads(json.dumps(e.DATOS))
    base["explicaciones"]["spo2"]["senales_a_vigilar"] = [{"texto": "x", "cita": "quote", "fuente": "https://ejemplo.com/a"}]
    f.write_text(json.dumps(base))
    with pytest.raises(e.ExplicacionesInvalidas):
        e.cargar(f)
