import copy

import pytest

from app.dominio import reglas
from app.dominio import umbrales as u
from app.dominio.catalogos import INDICADORES

ESTABLE = [70, 70, 71, 70, 70, 71, 70]          # serie casi constante: desviación estándar ~0.5


def test_sin_piso_una_serie_muy_estable_convierte_un_cambio_insignificante_en_aviso():
    """Este era el defecto: 5 latidos de diferencia disparaban un aviso por tener una desviación diminuta."""
    assert reglas.desviacion_linea_base(75, ESTABLE)["aviso"] is True


def test_con_piso_un_cambio_pequeno_ya_no_es_aviso_pero_uno_real_si():
    piso = reglas.piso_de("frecuencia_cardiaca")
    assert piso > 0
    assert reglas.desviacion_linea_base(75, ESTABLE, piso=piso)["aviso"] is False
    assert reglas.desviacion_linea_base(85, ESTABLE, piso=piso)["aviso"] is True        # +15 lpm sí es un cambio real


def test_el_piso_no_afecta_a_las_series_con_variacion_natural_mayor_que_el_piso():
    natural = [60, 75, 68, 80, 62, 77, 70]                                                # desviación ~7: mayor que cualquier piso
    sin, con = reglas.desviacion_linea_base(110, natural), reglas.desviacion_linea_base(110, natural, piso=4)
    assert sin["aviso"] == con["aviso"] and sin["desviacion_efectiva"] == con["desviacion_efectiva"] == sin["desviacion"]


def test_el_resultado_informa_la_desviacion_real_y_la_efectiva():
    r = reglas.desviacion_linea_base(75, ESTABLE, piso=4)
    assert r["desviacion"] < 1 and r["desviacion_efectiva"] == 4


def test_serie_constante_con_piso_ya_no_avisa_por_cualquier_diferencia():
    assert reglas.desviacion_linea_base(72, [70] * 6)["aviso"] is True                    # sin piso: cualquier cambio avisa
    assert reglas.desviacion_linea_base(72, [70] * 6, piso=4)["aviso"] is False
    assert reglas.desviacion_linea_base(90, [70] * 6, piso=4)["aviso"] is True


def test_el_piso_se_combina_con_solo_baja():
    assert reglas.desviacion_linea_base(120, [60, 60, 61, 60, 59, 60], solo_baja=True, piso=10)["aviso"] is False
    assert reglas.desviacion_linea_base(20, [60, 60, 61, 60, 59, 60], solo_baja=True, piso=10)["aviso"] is True


def test_todo_indicador_con_linea_base_tiene_su_piso_declarado():
    pisos = u.UMBRALES["linea_base"]["piso_desviacion"]
    assert (set(INDICADORES) - {"avpu"}) | {"animo"} <= set(pisos)                       # avpu no es numérico
    assert all(v > 0 for v in pisos.values())
    assert reglas.piso_de("inexistente") == 0.0


def test_el_archivo_rechaza_pisos_invalidos():
    d = copy.deepcopy(u.UMBRALES)
    d["linea_base"]["piso_desviacion"]["spo2"] = 0
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)
    d = copy.deepcopy(u.UMBRALES)
    d["linea_base"]["piso_desviacion"]["spo2"] = "mucho"
    with pytest.raises(u.UmbralesInvalidos):
        u.validar(d)


def test_en_la_api_un_cambio_pequeno_no_activa_el_aviso_pero_un_cambio_real_si(cliente):
    for v in (70, 70, 71, 70, 70, 71, 70):
        cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "frecuencia_cardiaca", "valor": v})
    pequeno = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "frecuencia_cardiaca", "valor": 75}).json()
    assert pequeno["aviso_linea_base"] is False
    real = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "frecuencia_cardiaca", "valor": 92}).json()
    assert real["aviso_linea_base"] is True
