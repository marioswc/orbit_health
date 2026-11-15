def test_listado_de_escenarios(cliente):
    ids = {e["id"] for e in cliente.get("/api/demo/escenarios").json()}
    assert {"hipoxia_eclipse", "co2_colectivo"} <= ids


def test_hipoxia_eclipse_retiene_y_reconexion_sale_primero_la_emergencia(cliente):
    r = cliente.post("/api/demo/escenarios/hipoxia_eclipse").json()
    assert r["pasos"][-3]["nivel"] == "rojo"
    cola = cliente.get("/api/cola").json()
    assert cola["enlace"]["activo"] is False
    assert all(i["estado"] == "retenido" for i in cola["items"][:3])     # nada salió en eclipse
    salida = cliente.post("/api/enlace", json={"activo": True, "entorno": "marte"}).json()["despachados"]
    prioridades = [d["prioridad"] for d in salida]
    assert prioridades == sorted(prioridades) and prioridades[0] == 1
    assert cliente.get("/api/cola/verificar").json()["valida"] is True


def test_reconectar_en_el_mismo_paso(cliente):
    r = cliente.post("/api/demo/escenarios/hipoxia_eclipse?reconectar=true").json()
    ultimo = r["pasos"][-1]
    assert ultimo["paso"] == "reconexion" and ultimo["orden_prioridades"][0] == 1


def test_co2_colectivo_dispara_la_alerta(cliente):
    cliente.post("/api/demo/escenarios/co2_colectivo")
    a = cliente.get("/api/alertas/colectivas").json()["alertas"]
    assert a and a[0]["afectados"] == 2


def test_o2_colectivo_dispara_alerta_hipoxia_ambiental(cliente):
    cliente.post("/api/demo/escenarios/o2_colectivo")
    res = cliente.get("/api/alertas/colectivas").json()
    ids = {a["id"] for a in res["alertas"]}
    assert "alerta_hipoxia_ambiental_colectiva" in ids
    assert res["o2_nivel"] == "amarillo"


def test_escenario_proceso_infeccioso_activa_regla_combinada(cliente):
    cliente.post("/api/demo/escenarios/proceso_infeccioso")
    estado = cliente.get("/api/estado/T2").json()
    assert "posible_proceso_infeccioso" in {r["id"] for r in estado["reglas_combinadas"]}


def test_escenario_desconocido_404(cliente):
    assert cliente.post("/api/demo/escenarios/nada").status_code == 404
