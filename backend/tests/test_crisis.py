import sqlite3

import pytest

from app import config
from app.dominio import crisis as dom
from app.dominio import reglas
from app.repositorios import conexion


def test_evaluacion_dominio_distingue_ninguno_seguimiento_y_crisis():
    neg = dom.evaluar_tamizaje(1, 1, riesgo_autolesion=False)
    assert neg["positivo"] is False and neg["nivel_protocolo"] == "ninguno" and neg["categorias_capsulas"] == ()
    assert neg["calidad_oxigeno"]["presente"] is False

    seg = dom.evaluar_tamizaje(2, 1, riesgo_autolesion=False)
    assert seg["positivo"] is True and seg["nivel_protocolo"] == "seguimiento"
    assert seg["categorias_capsulas"] == ("autorregulacion",)

    # Incluso con puntaje PHQ-2 bajo, el riesgo de autolesión activa el protocolo de crisis
    cri = dom.evaluar_tamizaje(0, 1, riesgo_autolesion=True)
    assert cri["positivo"] is True and cri["nivel_protocolo"] == "crisis"
    assert cri["categorias_capsulas"] == ("crisis", "autorregulacion")


def test_calidad_de_oxigeno_en_dominio_y_en_protocolo_de_crisis():
    assert reglas.evaluar_o2_cabina(21.0) == "verde"
    assert reglas.evaluar_o2_cabina(19.2) == "amarillo"
    assert reglas.evaluar_o2_cabina(18.5) == "rojo"
    assert reglas.evaluar_o2_cabina(23.2) == "amarillo"
    assert reglas.evaluar_o2_cabina(24.0) == "rojo"
    assert reglas.evaluar_ambiente(o2_pct=18.5) == "rojo"

    # Si la calidad de oxígeno es crítica (<19 %), el tamizaje escala a protocolo de crisis e incluye el paso de O2
    ev = dom.evaluar_tamizaje(0, 1, riesgo_autolesion=False, calidad_oxigeno=18.4)
    assert ev["positivo"] is True and ev["nivel_protocolo"] == "crisis"
    assert ev["calidad_oxigeno"] == {
        "presente": True, "valor_pct": 18.4, "nivel": "rojo", "alerta": True, "causa": "hipoxia_ambiental"
    }

    proto = dom.protocolo_crisis("crisis", tono="directo", calidad_oxigeno=18.4)
    assert proto["calidad_oxigeno"]["alerta"] is True
    assert "calidad de oxígeno en cabina (O₂: 18.4 %, nivel rojo)" in proto["pasos"][0]
    assert len(proto["pasos"]) == 5


def test_protocolo_adapta_el_tono_sin_recortar_pasos_de_seguridad():
    directo = dom.protocolo_crisis("crisis", tono="directo")
    calido = dom.protocolo_crisis("crisis", tono="calido")
    assert directo["urgencia"] == "inmediata" and len(directo["pasos"]) == 4
    assert len(calido["pasos"]) == 4 and directo["pasos"] != calido["pasos"]
    assert directo["estado_validacion"] == "pendiente_validacion_salud_mental"
    assert directo["transmitido_tierra"] is False and directo["privado"] is True


def test_validaciones_de_dominio():
    with pytest.raises(ValueError):
        dom.evaluar_tamizaje(4, 0)
    with pytest.raises(ValueError):
        dom.protocolo_crisis("inexistente")
    with pytest.raises(ValueError):
        dom.evaluar_calidad_oxigeno(5.0)  # fuera de rango [10, 35]


def test_indicador_o2_cabina_y_alerta_colectiva_de_hipoxia(cliente):
    r_ok = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "o2_cabina", "valor": 21.0})
    assert r_ok.status_code == 200 and r_ok.json()["nivel"] == "verde"

    r_bajo = cliente.post("/api/lecturas", json={"tripulante_id": "T3", "indicador": "o2_cabina", "valor": 18.6})
    assert r_bajo.status_code == 200 and r_bajo.json()["nivel"] == "rojo"

    # Dos tripulantes afectados + O2 de cabina bajo dispara la alerta colectiva de hipoxia ambiental
    cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 90})
    cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "spo2", "valor": 92})
    cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "frecuencia_respiratoria", "valor": 25})
    col = cliente.get("/api/alertas/colectivas").json()
    assert col["o2_pct"] == 18.6 and col["o2_nivel"] == "rojo"
    assert any(a["id"] == "alerta_hipoxia_ambiental_colectiva" for a in col["alertas"])


def test_tamizaje_y_protocolo_toman_en_cuenta_calidad_de_oxigeno_explicita_o_de_cabina(cliente):
    # 1. Con calidad_oxigeno explícita en el tamizaje
    r1 = cliente.post(
        "/api/tamizajes",
        json={"tripulante_id": "T1", "item1": 1, "item2": 1, "riesgo_autolesion": True, "calidad_oxigeno": 19.2},
    ).json()
    assert r1["nivel_protocolo"] == "crisis"
    assert r1["calidad_oxigeno"]["nivel"] == "amarillo" and r1["calidad_oxigeno"]["alerta"] is True
    assert "19.2 %" in r1["protocolo"]["pasos"][0]

    # 2. Tomando automáticamente la lectura vigente de o2_cabina en la nave
    cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "o2_cabina", "valor": 18.5})
    p = cliente.get("/api/crisis/protocolo?tripulante_id=T1&nivel=crisis").json()
    assert p["calidad_oxigeno"]["valor_pct"] == 18.5 and p["calidad_oxigeno"]["nivel"] == "rojo"
    assert "18.5 %" in p["pasos"][0]


def test_tamizaje_con_riesgo_activa_protocolo_crisis_y_no_encola(cliente):
    r = cliente.post(
        "/api/tamizajes",
        json={"tripulante_id": "T1", "item1": 1, "item2": 0, "riesgo_autolesion": True},
    ).json()
    assert r["positivo"] is True and r["riesgo_autolesion"] is True
    assert r["nivel_protocolo"] == "crisis"
    assert r["protocolo"]["urgencia"] == "inmediata" and len(r["protocolo"]["pasos"]) == 4
    assert any(c["id"].startswith("crisis-") for c in r["capsulas"])
    assert r["compartido_medico"] is False and r["transmitido_tierra"] is False
    assert cliente.get("/api/cola").json()["items"] == []


def test_protocolo_directo_respeta_preferencia_de_tono_del_tripulante(cliente):
    cliente.put("/api/preferencias/T1", json={"tono": "calido", "detalle": "breve", "recordatorios": "normal"})
    p = cliente.get("/api/crisis/protocolo?tripulante_id=T1&nivel=crisis").json()
    assert p["tono"] == "calido" and len(p["pasos"]) == 4 and p["capsulas"]
    assert "No tienes que pasar por esto a solas" in p["pasos"][0]


def test_sin_consentimiento_no_se_avisa_al_medico_ni_se_acepta_peticion(cliente):
    cliente.post("/api/tamizajes", json={"tripulante_id": "T1", "item1": 3, "item2": 3, "riesgo_autolesion": True})
    assert cliente.get("/api/crisis/avisos").json() == []
    r = cliente.post(
        "/api/crisis/aviso-medico",
        json={"tripulante_id": "T1", "consentimiento": False, "tipo": "crisis"},
    )
    assert r.status_code == 422
    neg = cliente.post(
        "/api/tamizajes",
        json={"tripulante_id": "T1", "item1": 0, "item2": 0, "compartir_medico": True},
    )
    assert neg.status_code == 422


def test_consentimiento_en_tamizaje_o_posterior_avisa_al_medico_sin_salir_a_tierra_ni_al_informe(cliente):
    tam = cliente.post(
        "/api/tamizajes",
        json={
            "tripulante_id": "T3",
            "item1": 2,
            "item2": 2,
            "compartir_medico": True,
            "mensaje_medico": "Prefiero hablar después del turno",
        },
    ).json()
    assert tam["compartido_medico"] is True and tam["aviso_medico_id"] is not None

    cri = cliente.post(
        "/api/crisis/aviso-medico",
        json={"tripulante_id": "T4", "consentimiento": True, "tipo": "crisis", "mensaje": "Necesito apoyo en cabina"},
    )
    assert cri.status_code == 200 and cri.json()["nivel_protocolo"] == "crisis"

    avisos = cliente.get("/api/crisis/avisos?solo_pendientes=true").json()
    assert [a["tripulante_id"] for a in avisos] == ["T4", "T3"]
    assert [a["nivel_protocolo"] for a in avisos] == ["crisis", "seguimiento"]

    conn = sqlite3.connect(config.DB_PATH)
    assert conn.execute("SELECT COUNT(*) FROM cola_salida").fetchone()[0] == 0
    conn.close()
    for url in ("/api/informe", "/api/informe/T3", "/api/informe/T4"):
        texto = cliente.get(url).text
        assert "Prefiero hablar" not in texto and "Necesito apoyo" not in texto


def test_revocar_consentimiento_oculta_el_aviso_al_medico_y_atender_queda_auditado(cliente):
    av1 = cliente.post(
        "/api/crisis/aviso-medico",
        json={"tripulante_id": "T3", "consentimiento": True, "tipo": "tamizaje_positivo"},
    ).json()
    av2 = cliente.post(
        "/api/crisis/aviso-medico",
        json={"tripulante_id": "T4", "consentimiento": True, "tipo": "crisis"},
    ).json()

    rev = cliente.post(f"/api/crisis/avisos/{av1['id']}/revocar", json={"tripulante_id": "T3"})
    assert rev.status_code == 200 and rev.json()["estado"] == "revocado"
    assert [a["id"] for a in cliente.get("/api/crisis/avisos").json()] == [av2["id"]]
    assert cliente.get("/api/crisis/avisos/T3").json()[0]["estado"] == "revocado"

    assert cliente.post(f"/api/crisis/avisos/{av1['id']}/atender").status_code == 404
    at = cliente.post(f"/api/crisis/avisos/{av2['id']}/atender")
    assert at.status_code == 200 and at.json()["estado"] == "atendido"
    assert cliente.get("/api/crisis/avisos?solo_pendientes=true").json() == []


def test_permisos_de_protocolo_y_avisos_con_autenticacion(cliente_auth):
    c = cliente_auth
    h1 = c.entrar("T1")  # comandante
    h2 = c.entrar("T2")  # tripulante
    h3 = c.entrar("T3")  # tripulante
    h4 = c.entrar("T4")  # tripulante

    assert c.post("/api/crisis/aviso-medico", json={"tripulante_id": "T3", "consentimiento": True}, headers=h4).status_code == 403
    av = c.post("/api/crisis/aviso-medico", json={"tripulante_id": "T3", "consentimiento": True, "tipo": "crisis"}, headers=h3).json()
    assert c.get("/api/crisis/avisos/T3", headers=h2).status_code == 403          # otro astronauta no ve avisos ajenos
    assert c.post(f"/api/crisis/avisos/{av['id']}/revocar", json={"tripulante_id": "T3"}, headers=h2).status_code == 403

    assert c.get("/api/crisis/avisos", headers=h4).status_code == 403
    assert c.post(f"/api/crisis/avisos/{av['id']}/atender", headers=h4).status_code == 403

    assert c.get("/api/crisis/avisos", headers=h2).status_code == 403          # solo el comandante ve la lista
    lista = c.get("/api/crisis/avisos", headers=h1).json()
    assert len(lista) == 1 and lista[0]["id"] == av["id"]
    at = c.post(f"/api/crisis/avisos/{av['id']}/atender", headers=h1).json()
    assert at["estado"] == "atendido" and at["atendido_por"] == "T1"

    aud = c.get("/api/auditoria", headers=h1).json()
    acciones = {a["accion"] for a in aud}
    assert "consentimiento_salud_mental" in acciones and "atencion_salud_mental" in acciones
    assert c.get("/api/auditoria/verificar", headers=h1).json()["valida"] is True


def test_migracion_de_base_antigua_agrega_columnas_a_tamizajes(tmp_path):
    db = str(tmp_path / "vieja.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE tamizajes (id INTEGER PRIMARY KEY, tripulante_id TEXT, item1 INTEGER, item2 INTEGER, total INTEGER, ts TEXT)")
    conn.commit()
    conn.close()

    conexion.init_db(db)
    conn = sqlite3.connect(db)
    cols = {f[1] for f in conn.execute("PRAGMA table_info(tamizajes)")}
    conn.close()
    assert {"riesgo_autolesion", "calidad_oxigeno", "nivel_protocolo"} <= cols
