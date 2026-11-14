from app.dominio import peligros as p
from app.dominio import reglas

HABITUAL = [60, 62, 58, 61, 59, 60]


def lectura(c, ind, val, tid="T1"):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val})


def prepara(c, ind, valores, tid="T1"):
    for v in valores:
        lectura(c, ind, v, tid)


def test_ejercicio_es_indicador_sin_umbral_absoluto(cliente):
    assert "ejercicio_min" in {i["clave"] for i in cliente.get("/api/indicadores").json()}
    for minutos in (0, 30, 600):
        assert lectura(cliente, "ejercicio_min", minutos, tid="T2").json()["nivel"] == "verde"
    assert lectura(cliente, "ejercicio_min", 601).status_code == 422


def test_hacer_menos_ejercicio_que_lo_habitual_da_aviso(cliente):
    prepara(cliente, "ejercicio_min", HABITUAL)
    r = lectura(cliente, "ejercicio_min", 15).json()
    assert r["aviso_linea_base"] is True and r["nivel"] == "amarillo"


def test_hacer_mas_ejercicio_que_lo_habitual_no_es_aviso(cliente):
    prepara(cliente, "ejercicio_min", HABITUAL)
    r = lectura(cliente, "ejercicio_min", 120).json()
    assert r["aviso_linea_base"] is False and r["nivel"] == "verde"


def test_dormir_mas_de_lo_habitual_no_es_aviso_pero_dormir_menos_si(cliente):
    prepara(cliente, "sueno_horas", [7, 7.5, 7, 6.8, 7.2, 7])
    assert lectura(cliente, "sueno_horas", 10.5).json()["aviso_linea_base"] is False


def test_dormir_muy_por_debajo_de_su_base_da_aviso(cliente):
    prepara(cliente, "sueno_horas", [8, 8, 8.2, 7.9, 8.1, 8], tid="T2")
    r = lectura(cliente, "sueno_horas", 6.5, tid="T2").json()
    assert r["aviso_linea_base"] is True and r["nivel"] == "amarillo"


def test_un_animo_mejor_que_el_habitual_no_ofrece_apoyo_y_uno_peor_si(cliente):
    for v in (3, 3, 4, 3, 3, 3):
        cliente.post("/api/animo", json={"tripulante_id": "T3", "valor": v})
    assert cliente.post("/api/animo", json={"tripulante_id": "T3", "valor": 5}).json()["capsulas"] == []
    for v in (4, 4, 5, 4, 4, 4):
        cliente.post("/api/animo", json={"tripulante_id": "T4", "valor": v})
    peor = cliente.post("/api/animo", json={"tripulante_id": "T4", "valor": 3}).json()
    assert peor["aviso_linea_base"] is True and peor["capsulas"]


def test_reglas_solo_baja_en_el_dominio():
    hist = [60, 62, 58, 61, 59, 60]
    assert reglas.desviacion_linea_base(120, hist)["aviso"] is True                     # por defecto, ambos lados
    assert reglas.desviacion_linea_base(120, hist, solo_baja=True)["aviso"] is False
    assert reglas.desviacion_linea_base(20, hist, solo_baja=True)["aviso"] is True
    # serie constante: sigma 0, solo avisa si baja
    assert reglas.desviacion_linea_base(80, [60] * 6, solo_baja=True)["aviso"] is False
    assert reglas.desviacion_linea_base(40, [60] * 6, solo_baja=True)["aviso"] is True


def test_el_estado_aplica_la_misma_regla_unilateral(cliente):
    prepara(cliente, "ejercicio_min", HABITUAL)
    lectura(cliente, "ejercicio_min", 150)
    ind = {i["indicador"]: i for i in cliente.get("/api/estado/T1").json()["indicadores"]}
    assert ind["ejercicio_min"]["linea_base"]["aviso"] is False


def test_la_cobertura_del_hrp_sube_a_ocho_de_diecisiete_y_sigue_siendo_honesta():
    r = p.resumen_cobertura()
    assert r == {"total": 17, "cubierto": 1, "parcial": 7, "no_cubierto": 9}
    riesgo = next(x for x in p.DATOS["riesgos"] if "Reduced Cardiorespiratory" in x["nombre_oficial"])
    assert riesgo["cobertura"] == "parcial" and "no mide la condición física" in riesgo["nota"]
    assert p.peligros_de(["ejercicio_min"])[0]["id"] == "campos_gravedad"


def test_hay_explicacion_y_peligro_para_el_ejercicio(cliente):
    una = cliente.get("/api/explicaciones/ejercicio_min").json()
    assert "ejercicio" in una["que_es"].lower() and una["fuentes"]
    r = lectura(cliente, "ejercicio_min", 0, tid="T3").json()      # sin base previa: verde y sin peligro relacionado
    assert r["nivel"] == "verde" and r["peligros_relacionados"] == []
