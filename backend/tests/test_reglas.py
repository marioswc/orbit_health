import importlib

import pytest

from app.dominio import reglas as engine

NORMAL = dict(frecuencia_respiratoria=16, spo2=98, presion_sistolica=120,
              frecuencia_cardiaca=70, avpu="A", temperatura=36.8)


def test_normal_es_verde_cero():
    r = engine.evaluar_news2(NORMAL)
    assert (r.puntos, r.nivel) == (0, "verde")


@pytest.mark.parametrize("campo,valor,esperado", [
    ("frecuencia_respiratoria", 8, 3), ("frecuencia_respiratoria", 9, 1),
    ("frecuencia_respiratoria", 20, 0), ("frecuencia_respiratoria", 21, 2),
    ("frecuencia_respiratoria", 25, 3),
    ("spo2", 91, 3), ("spo2", 92, 2), ("spo2", 94, 1), ("spo2", 96, 0),
    ("presion_sistolica", 90, 3), ("presion_sistolica", 100, 2),
    ("presion_sistolica", 110, 1), ("presion_sistolica", 111, 0),
    ("presion_sistolica", 220, 3),
    ("frecuencia_cardiaca", 40, 3), ("frecuencia_cardiaca", 50, 1),
    ("frecuencia_cardiaca", 91, 1), ("frecuencia_cardiaca", 111, 2),
    ("frecuencia_cardiaca", 131, 3),
    ("avpu", "V", 3),
    ("temperatura", 35.0, 3), ("temperatura", 35.5, 1), ("temperatura", 38.0, 0),
    ("temperatura", 38.5, 1), ("temperatura", 39.1, 2),
])
def test_puntos_por_variable(campo, valor, esperado):
    r = engine.evaluar_news2({**NORMAL, campo: valor})
    assert r.desglose[campo] == esperado


def test_temperatura_alta_no_es_roja_aislada():
    r = engine.evaluar_news2({**NORMAL, "temperatura": 39.5})
    assert (r.puntos, r.nivel) == (2, "verde")


def test_total_7_es_rojo():
    r = engine.evaluar_news2({**NORMAL, "frecuencia_respiratoria": 22, "spo2": 93,
                              "presion_sistolica": 100, "frecuencia_cardiaca": 115,
                              "temperatura": 38.5})
    assert r.puntos == 9 and r.nivel == "rojo"


def test_extremo_aislado_modo_conservador():
    r = engine.evaluar_news2({**NORMAL, "spo2": 90})
    assert r.nivel == "rojo" and r.extremos == ["spo2"]


def test_extremo_aislado_modo_rcp(monkeypatch):
    monkeypatch.setattr(engine, "MODO_PARAMETRO_EXTREMO", "rcp")
    assert engine.evaluar_news2({**NORMAL, "spo2": 90}).nivel == "amarillo"


def test_5_o_6_amarillo():
    r = engine.evaluar_news2({**NORMAL, "frecuencia_respiratoria": 22, "spo2": 93,
                              "frecuencia_cardiaca": 95, "temperatura": 38.5})
    assert r.puntos == 6 and r.nivel == "amarillo"


def test_faltantes_se_reportan():
    r = engine.evaluar_news2({"spo2": 98})
    assert "temperatura" in r.faltantes and r.puntos == 0


@pytest.mark.parametrize("co2,dosis,esperado", [
    (3.0, 10, "verde"), (3.1, 10, "amarillo"), (4.0, 10, "amarillo"),
    (4.1, 10, "rojo"), (2.0, 70, "amarillo"), (2.0, 90, "rojo"),
])
def test_ambiente(co2, dosis, esperado):
    assert engine.evaluar_ambiente(co2, dosis) == esperado


def test_linea_base_sin_muestras_suficientes():
    assert engine.desviacion_linea_base(80, [70, 71])["aplica"] is False


def test_linea_base_aviso_a_mas_de_2_de():
    hist = [70, 72, 68, 71, 69, 70, 71]
    assert engine.desviacion_linea_base(90, hist)["aviso"] is True
    assert engine.desviacion_linea_base(71, hist)["aviso"] is False
