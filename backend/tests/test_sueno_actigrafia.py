from app.dominio import reglas

HAB_EFIC = [90, 91, 89, 90, 92, 90]
HAB_DESP = [25, 28, 22, 26, 24, 27]


def lectura(c, ind, val, tid="T1"):
    return c.post("/api/lecturas", json={"tripulante_id": tid, "indicador": ind, "valor": val})


def prepara(c, ind, valores):
    for v in valores:
        lectura(c, ind, v)


def test_son_indicadores_sin_umbral_absoluto_y_con_rango_de_captura(cliente):
    claves = {i["clave"] for i in cliente.get("/api/indicadores").json()}
    assert {"sueno_eficiencia_pct", "sueno_despertares_min"} <= claves
    assert lectura(cliente, "sueno_eficiencia_pct", 40, "T2").json()["nivel"] == "verde"
    assert lectura(cliente, "sueno_despertares_min", 300, "T2").json()["nivel"] == "verde"
    assert lectura(cliente, "sueno_eficiencia_pct", 101).status_code == 422
    assert lectura(cliente, "sueno_despertares_min", 601).status_code == 422


def test_eficiencia_mucho_menor_que_la_habitual_da_aviso_y_mayor_no(cliente):
    prepara(cliente, "sueno_eficiencia_pct", HAB_EFIC)
    assert lectura(cliente, "sueno_eficiencia_pct", 99).json()["aviso_linea_base"] is False
    assert lectura(cliente, "sueno_eficiencia_pct", 70).json()["aviso_linea_base"] is True


def test_mas_tiempo_despierto_que_lo_habitual_da_aviso_y_menos_no(cliente):
    prepara(cliente, "sueno_despertares_min", HAB_DESP)
    assert lectura(cliente, "sueno_despertares_min", 5).json()["aviso_linea_base"] is False
    r = lectura(cliente, "sueno_despertares_min", 90).json()
    assert r["aviso_linea_base"] is True and r["nivel"] == "amarillo"


def test_solo_alta_en_la_funcion_pura():
    h = [25, 28, 22, 26, 24, 27]
    assert reglas.desviacion_linea_base(5, h, solo_alta=True, piso=10)["aviso"] is False
    assert reglas.desviacion_linea_base(90, h, solo_alta=True, piso=10)["aviso"] is True
    assert reglas.desviacion_linea_base(5, h, piso=10)["aviso"] is True      # sin la opción, ambos lados avisan
