def test_sin_sesion_no_se_accede_a_datos_clinicos(cliente_auth):
    c = cliente_auth
    assert c.get("/api/estado/T1").status_code == 401
    assert c.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 98}).status_code == 401
    assert c.get("/api/cola").status_code == 401
    assert c.post("/api/enlace", json={"activo": False, "entorno": "marte"}).status_code == 401


def test_rutas_publicas_siguen_abiertas_para_poder_iniciar_sesion(cliente_auth):
    c = cliente_auth
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/auth/estado").json()["activa"] is True
    assert c.get("/api/tripulantes").status_code == 200       # el selector de acceso necesita los nombres
    assert c.get("/api/umbrales").status_code == 200


def test_login_incorrecto_401_y_bloqueo_423(cliente_auth, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "MAX_INTENTOS", 3)
    c = cliente_auth
    for _ in range(3):
        assert c.post("/api/auth/login", json={"tripulante_id": "T3", "pin": "000000"}).status_code == 401
    r = c.post("/api/auth/login", json={"tripulante_id": "T3", "pin": "333333"})
    assert r.status_code == 423 and r.json()["detail"]["bloqueado_hasta"]


def test_cualquier_tripulante_puede_registrar_signos_de_un_companero_y_queda_auditado(cliente_auth):
    c = cliente_auth
    h3 = c.entrar("T3")
    r = c.post("/api/lecturas", json={"tripulante_id": "T4", "indicador": "avpu", "valor": 1}, headers=h3)
    assert r.status_code == 200 and r.json()["nivel"] == "rojo"            # compañero incapacitado: se registra y alerta
    assert c.get("/api/estado/T4", headers=h3).status_code == 200          # y cualquiera puede ver el estado clínico
    aud = c.get("/api/auditoria", headers=c.entrar("T1")).json()
    assert any(a["accion"] == "lectura_a_tercero" and a["actor"] == "T3" for a in aud)


def test_diario_y_phq2_solo_para_su_dueno_incluso_el_comandante(cliente_auth):
    c = cliente_auth
    h3 = c.entrar("T3")
    assert c.post("/api/diario", json={"tripulante_id": "T3", "contenido": "nota"}, headers=h3).status_code == 200
    assert c.get("/api/diario/T3", headers=h3).status_code == 200
    for otro in ("T1", "T2", "T4"):
        h = c.entrar(otro)
        assert c.get("/api/diario/T3", headers=h).status_code == 403
        assert c.post("/api/tamizajes", json={"tripulante_id": "T3", "item1": 3, "item2": 3}, headers=h).status_code == 403
    assert c.post("/api/tamizajes", json={"tripulante_id": "T3", "item1": 3, "item2": 3}, headers=h3).status_code == 200


def test_solo_el_comandante_cambia_el_enlace(cliente_auth):
    c = cliente_auth
    cuerpo = {"activo": False, "entorno": "marte"}
    assert c.post("/api/enlace", json=cuerpo, headers=c.entrar("T3")).status_code == 403
    assert c.post("/api/enlace", json=cuerpo, headers=c.entrar("T2")).status_code == 403          # otro astronauta no puede
    assert c.post("/api/enlace", json=cuerpo, headers=c.entrar("T1")).status_code == 200
    assert c.post("/api/enlace", json={"activo": True, "entorno": "marte"}, headers=c.entrar("T1")).status_code == 200
    aud = c.get("/api/auditoria", headers=c.entrar("T1")).json()
    assert sum(1 for a in aud if a["accion"] == "enlace_cambio") == 2


def test_auditoria_solo_para_el_comandante_y_es_verificable(cliente_auth):
    c = cliente_auth
    assert c.get("/api/auditoria", headers=c.entrar("T3")).status_code == 403
    assert c.get("/api/auditoria/verificar", headers=c.entrar("T1")).json()["valida"] is True


def test_logout_invalida_la_sesion(cliente_auth):
    c = cliente_auth
    h = c.entrar("T3")
    assert c.get("/api/auth/yo", headers=h).json() == {"tripulante_id": "T3", "rol": "tripulante"}
    c.post("/api/auth/logout", headers=h)
    assert c.get("/api/auth/yo", headers=h).status_code == 401


def test_reinicio_de_pin_por_el_comandante_y_recuperacion_con_codigo(cliente_auth):
    c = cliente_auth
    assert c.post("/api/auth/reiniciar-pin/T3", headers=c.entrar("T4")).status_code == 403
    nuevo = c.post("/api/auth/reiniciar-pin/T3", headers=c.entrar("T1")).json()["pin_temporal"]
    assert c.post("/api/auth/login", json={"tripulante_id": "T3", "pin": nuevo}).status_code == 200
    assert c.post("/api/auth/login", json={"tripulante_id": "T3", "pin": "333333"}).status_code == 401
    r = c.post("/api/auth/recuperar", json={"tripulante_id": "T3", "codigo_recuperacion": "AAAA-BBBB-CCCC", "pin_nuevo": "555555"})
    assert r.status_code == 401


def test_con_la_autenticacion_apagada_todo_sigue_funcionando(cliente):
    assert cliente.get("/api/auth/estado").json()["activa"] is False
    assert cliente.get("/api/estado/T1").status_code == 200
    assert cliente.post("/api/diario", json={"tripulante_id": "T1", "contenido": "x"}).status_code == 200
