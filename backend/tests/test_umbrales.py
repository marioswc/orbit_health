import copy
import json

import pytest

from app.dominio import umbrales as u


def test_archivo_por_defecto_es_valido():
    d = u.cargar()
    assert d["estado"].startswith("pendiente")
    assert set(u.NEWS2_VARIABLES) <= set(d["news2"]["bandas"])


def test_rechaza_bandas_no_crecientes():
    d = copy.deepcopy(u.UMBRALES)
    d["news2"]["bandas"]["spo2"] = [{"hasta": 95, "puntos": 1}, {"hasta": 91, "puntos": 3}, {"puntos": 0}]
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)


def test_rechaza_ultima_banda_con_hasta():
    d = copy.deepcopy(u.UMBRALES)
    d["news2"]["bandas"]["spo2"] = [{"hasta": 91, "puntos": 3}, {"hasta": 100, "puntos": 0}]
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)


def test_rechaza_seccion_faltante_y_modo_invalido():
    d = copy.deepcopy(u.UMBRALES); del d["ambiente"]
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)
    d = copy.deepcopy(u.UMBRALES); d["news2"]["modo_parametro_extremo"] = "otro"
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)


def test_archivo_ilegible(tmp_path):
    malo = tmp_path / "x.json"; malo.write_text("{no es json")
    with pytest.raises(u.UmbralesInvalidos):
        u.cargar(malo)


def test_json_equivale_a_tabla_oficial_en_valores_enteros():
    """Barrido de enteros contra la tabla de referencia escrita a mano."""
    from app.dominio import reglas as r
    ref_fr = lambda v: 3 if v <= 8 or v >= 25 else 2 if v >= 21 else 1 if v <= 11 else 0
    ref_fc = lambda v: 3 if v <= 40 or v >= 131 else 2 if v >= 111 else 1 if v <= 50 or v >= 91 else 0
    for v in range(4, 61):
        assert r._puntaje("frecuencia_respiratoria", v) == ref_fr(v)
    for v in range(20, 251):
        assert r._puntaje("frecuencia_cardiaca", v) == ref_fc(v)
