import pytest

from app.dominio import comparativa as c

PASOS = ["Repite la medición ahora.", "Avisa al médico."]


def test_la_ventana_sin_apoyo_es_ida_vuelta_mas_lo_que_tarda_tierra():
    r = c.linea_de_tiempo(1200, 60, "rojo", PASOS)
    assert r["ventana_sin_apoyo_s"] == 2 * 1200 + 60 and r["ventana_sin_apoyo_min"] == 41.0


def test_con_orbit_hay_accion_a_los_cero_segundos_y_sin_orbit_no():
    r = c.linea_de_tiempo(180, 60, "rojo", PASOS)
    assert [e["t_s"] for e in r["con_orbit"][:3]] == [0, 0, 0]
    assert r["sin_orbit"][0]["t_s"] == 0 and "sin clasificación" in r["sin_orbit"][0]["texto"]
    assert r["con_orbit"][-1]["t_s"] == r["sin_orbit"][-1]["t_s"] == 2 * 180 + 60   # la respuesta de Tierra llega igual


def test_aplica_el_factor_de_aceleracion_a_la_version_demo():
    r = c.linea_de_tiempo(1200, 0, "rojo", PASOS, factor_aceleracion=30)
    ack = [e for e in r["con_orbit"] if "confirmación" in e["texto"]][0]
    assert ack["t_s"] == 2400 and ack["t_demo_s"] == 80


def test_se_declara_ilustracion():
    r = c.linea_de_tiempo(10, 0, "verde", PASOS)
    assert r["tipo"] == "ilustracion" and "no una medición" in r["aviso"]


def test_endpoint_compara_marte_cercano_con_marte(cliente):
    cerca = cliente.get("/api/demo/comparativa?entorno=marte_cercano").json()
    lejos = cliente.get("/api/demo/comparativa?entorno=marte").json()
    assert cerca["ventana_sin_apoyo_min"] == 7.0 and lejos["ventana_sin_apoyo_min"] == 41.0
    assert cerca["con_orbit"][0]["texto"].startswith("La lectura se registra") and "rojo" in cerca["con_orbit"][0]["texto"]


@pytest.mark.parametrize("q", ["entorno=jupiter", "respuesta_tierra_min=-1"])
def test_endpoint_valida_parametros(cliente, q):
    assert cliente.get(f"/api/demo/comparativa?{q}").status_code == 422


def test_endpoint_no_escribe_datos(cliente):
    cliente.get("/api/demo/comparativa")
    assert cliente.get("/api/cola").json()["items"] == []
