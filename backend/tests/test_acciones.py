from app.dominio.acciones import acciones_sugeridas as a


def test_rojo_pide_repetir_avisar_y_explica_la_cola():
    p = a("rojo", 5)
    assert "Repite la medición ahora" in p[0] and "al comandante o a un compañero" in p[1]
    assert "prioridad máxima" in p[2] and p[-1] == "Próxima captura recomendada en 5 min."


def test_amarillo_es_mas_suave_y_verde_solo_indica_la_proxima_captura():
    assert a("amarillo", 15)[0] == "Repite la medición para confirmarla."
    assert a("verde", 60) == ["Próxima captura recomendada en 60 min."]


def test_incluye_reglas_observacion_linea_base_y_faltantes_con_nombres_legibles():
    p = a("amarillo", 15, observacion=True, aviso_linea_base=True, faltantes=["spo2", "temperatura"],
          reglas=[{"nombre": "Pulso elevado con presión sistólica baja"}], etiquetas={"spo2": "SpO₂", "temperatura": "Temperatura"})
    texto = " ".join(p)
    assert "Combinación detectada: Pulso elevado" in texto and "en observación" in texto
    assert "últimos 14 días" in texto and "SpO₂, Temperatura" in texto


def test_faltantes_no_se_reportan_en_verde():
    assert "Faltan" not in " ".join(a("verde", 60, faltantes=["spo2"]))


def test_nunca_sugiere_tratamiento_ni_medicacion():
    texto = " ".join(a("rojo", 5, observacion=True, aviso_linea_base=True, faltantes=["spo2"],
                       reglas=[{"nombre": "x"}])).lower()
    for prohibida in ("administra", "dosis", "medicamento", "toma ", "inyec", "oxígeno suplementario"):
        assert prohibida not in texto


def test_integrado_en_la_api(cliente):
    r = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88}).json()
    assert r["acciones_sugeridas"][0].startswith("Repite la medición ahora") and r["nivel"] == "rojo"
    e = cliente.get("/api/estado/T1").json()
    assert any("Faltan signos" in x for x in e["acciones_sugeridas"])
    v = cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "spo2", "valor": 98}).json()
    assert v["acciones_sugeridas"] == ["Te sugiero volver a medir en 60 min."]      # T2 tiene sembrado el trato cálido
