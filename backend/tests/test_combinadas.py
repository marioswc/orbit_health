import copy

import pytest

from app.dominio import combinadas as c
from app.dominio import umbrales as u


def test_ortostatica_requiere_ambos_datos():
    assert c.evaluar_individuales({"frecuencia_cardiaca": 105}) == []
    activas = c.evaluar_individuales({"frecuencia_cardiaca": 105, "presion_sistolica": 98})
    assert [a["id"] for a in activas] == ["posible_intolerancia_ortostatica"]


def test_infecciosa_y_bordes():
    assert c.evaluar_individuales({"temperatura": 38.0, "frecuencia_cardiaca": 100}) == []
    assert c.evaluar_individuales({"temperatura": 38.1, "frecuencia_cardiaca": 91})[0]["id"] == "posible_proceso_infeccioso"
    assert c.evaluar_individuales({"temperatura": 38.5, "frecuencia_cardiaca": 90}) == []


def test_normal_no_activa_nada():
    assert c.evaluar_individuales({"temperatura": 36.8, "frecuencia_cardiaca": 70, "presion_sistolica": 120}) == []


def test_colectiva_necesita_co2_y_dos_afectados():
    assert c.evaluar_colectiva(["amarillo", "rojo", "verde"], 3.5)["afectados"] == 2
    assert c.evaluar_colectiva(["amarillo", "verde", "verde"], 3.5) is None      # solo 1
    assert c.evaluar_colectiva(["rojo", "rojo"], 3.0) is None                    # CO2 no supera
    assert c.evaluar_colectiva(["rojo", "rojo"], None) is None                   # sin dato de CO2
    assert c.evaluar_colectiva(["rojo", "rojo"], 4.5)["nivel"] == "rojo"


def test_peor_nivel():
    assert c.peor_nivel(["verde", "amarillo"]) == "amarillo"
    assert c.peor_nivel([]) == "verde"


def test_validacion_rechaza_reglas_mal_formadas():
    d = copy.deepcopy(u.UMBRALES)
    d["reglas_combinadas"]["individuales"][0]["condiciones"][0]["indicador"] = "inventado"
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)
    d = copy.deepcopy(u.UMBRALES)
    d["reglas_combinadas"]["individuales"][0]["condiciones"][0]["op"] = "=="
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)
    d = copy.deepcopy(u.UMBRALES)
    d["reglas_combinadas"]["colectiva_co2"]["nivel"] = "morado"
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)
