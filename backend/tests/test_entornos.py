import copy
import json

import pytest

from app.api.referencia import RUTAS_PUBLICAS
from app.dominio import entornos as en
from app.dominio import enlace as modelo_enlace


def test_la_estimacion_osea_solo_aplica_en_microgravedad():
    for clave, x in en.DATOS["entornos"].items():
        if x["microgravedad"]:
            assert x["gravedad_g"] == 0 and x["estimacion_osea"]["estado"] == "aplica", clave
        else:
            assert x["estimacion_osea"]["estado"] == "no_caracterizada", clave


def test_la_gravedad_de_marte_es_la_que_dice_la_nasa_tres_octavos():
    assert en.DATOS["entornos"]["base_marciana"]["gravedad_g"] == pytest.approx(3 / 8)
    assert "tres octavos" in en.DATOS["entornos"]["base_marciana"]["estimacion_osea"]["nota"]
    assert en.DATOS["fuente_gravedad"].startswith("https://www.nasa.gov/")


def test_el_rover_no_inventa_una_gravedad_porque_depende_del_cuerpo():
    assert en.DATOS["entornos"]["rover_en_superficie"]["gravedad_g"] is None


def test_cada_entorno_dice_que_no_se_calcula_la_perdida_osea_cuando_no_hay_cifra():
    for clave, x in en.DATOS["entornos"].items():
        if x["estimacion_osea"]["estado"] == "no_caracterizada":
            assert "no se calcula" in x["estimacion_osea"]["nota"] or "no hay cifras" in x["estimacion_osea"]["nota"], clave


def test_los_perfiles_de_enlace_tipicos_existen_en_el_modelo_de_enlace():
    conocidos = set(modelo_enlace.entornos())
    for clave, x in en.DATOS["entornos"].items():
        assert set(x["perfil_enlace_tipico"]) <= conocidos, clave


def test_el_archivo_rechaza_combinaciones_incoherentes(tmp_path):
    base = copy.deepcopy(en.DATOS)
    base["entornos"]["base_lunar"]["estimacion_osea"]["estado"] = "aplica"            # cifra de microgravedad en gravedad parcial
    f = tmp_path / "e.json"; f.write_text(json.dumps(base))
    with pytest.raises(en.EntornosInvalidos):
        en.cargar(f)
    base = copy.deepcopy(en.DATOS)
    base["entornos"]["nave_en_transito"]["gravedad_g"] = 0.5                          # microgravedad con gravedad
    f.write_text(json.dumps(base))
    with pytest.raises(en.EntornosInvalidos):
        en.cargar(f)
    base = copy.deepcopy(en.DATOS)
    base["entornos"]["base_lunar"]["gravedad_g"] = -1
    f.write_text(json.dumps(base))
    with pytest.raises(en.EntornosInvalidos):
        en.cargar(f)


def test_endpoints_publicos_y_declarados_como_tales(cliente):
    assert ("GET", "/api/entornos") in RUTAS_PUBLICAS and ("GET", "/api/entornos/{clave}") in RUTAS_PUBLICAS
    todos = cliente.get("/api/entornos").json()
    assert set(todos["entornos"]) == set(en.DATOS["entornos"])
    uno = cliente.get("/api/entornos/base_marciana").json()
    assert uno["gravedad_g"] == pytest.approx(0.375) and uno["estimacion_osea"]["estado"] == "no_caracterizada"
    assert cliente.get("/api/entornos/luna_de_queso").status_code == 404
