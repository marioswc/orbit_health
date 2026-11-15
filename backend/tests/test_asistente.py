import pytest

from app.dominio import acciones as a

ROJO = dict(nivel="rojo", proxima_captura_min=5, observacion=True, aviso_linea_base=True, faltantes=["spo2"],
            reglas=[{"nombre": "X"}], etiquetas={"spo2": "SpO₂"})


def test_el_tono_cambia_la_forma_no_el_contenido():
    directo = a.acciones_sugeridas(**ROJO, tono="directo")
    calido = a.acciones_sugeridas(**ROJO, tono="calido")
    assert directo != calido and len(directo) == len(calido)            # mismos pasos, distinta redacción
    assert any("al comandante" in t for t in calido)                # el aviso urgente sigue ahí


def test_el_modo_breve_quita_explicaciones_pero_conserva_todos_los_avisos():
    breve = " ".join(a.acciones_sugeridas(**ROJO, detalle="breve")).lower()
    completo = " ".join(a.acciones_sugeridas(**ROJO, detalle="completo")).lower()
    assert len(breve) < len(completo)
    for imprescindible in ("repite", "avisa", "próxima captura"):
        assert imprescindible in breve
    assert "prioridad máxima" not in breve and "prioridad máxima" in completo


@pytest.mark.parametrize("tono", a.TONOS)
@pytest.mark.parametrize("detalle", a.DETALLES)
@pytest.mark.parametrize("nivel", ["rojo", "amarillo"])
def test_ningun_estilo_omite_el_paso_de_avisar_ni_la_repeticion(tono, detalle, nivel):
    texto = " ".join(a.acciones_sugeridas(nivel, 15, tono=tono, detalle=detalle)).lower()
    assert ("avisa" in texto or "cuéntaselo" in texto or "avisa ahora" in texto)
    assert "medir" in texto or "repite" in texto


def test_ningun_estilo_sugiere_tratamiento_ni_medicacion():
    prohibidas = ("administra", "dosis de", "medicamento", "toma ", "inyec", "fármaco", "farmaco")
    for tono in a.TONOS:
        for detalle in a.DETALLES:
            t = " ".join(a.acciones_sugeridas(**ROJO, tono=tono, detalle=detalle)).lower()
            assert not any(p in t for p in prohibidas)


def test_tono_desconocido_cae_al_directo():
    assert a.renderizar([{"clave": "repetir"}], tono="raro") == a.renderizar([{"clave": "repetir"}], tono="directo")


def test_recordatorios_frecuente_acorta_y_minimo_solo_alarga_en_verde():
    assert a.ajustar_intervalo(60, "verde", "frecuente") == 30
    assert a.ajustar_intervalo(5, "rojo", "frecuente") == 2.5
    assert a.ajustar_intervalo(60, "verde", "minimo") == 90
    assert a.ajustar_intervalo(5, "rojo", "minimo") == 5               # nunca se alarga una emergencia
    assert a.ajustar_intervalo(15, "amarillo", "minimo") == 15
    assert a.ajustar_intervalo(60, "verde", "normal") == 60
    assert a.ajustar_intervalo(1, "rojo", "frecuente") == 1.0           # nunca por debajo de 1 minuto


def test_preferencias_por_defecto_y_guardado(cliente):
    assert cliente.get("/api/preferencias/T1").json() == {"tono": "directo", "detalle": "completo", "recordatorios": "normal"}
    r = cliente.put("/api/preferencias/T1", json={"tono": "calido", "detalle": "breve", "recordatorios": "frecuente"})
    assert r.status_code == 200 and r.json()["tono"] == "calido"
    assert cliente.get("/api/preferencias/T1").json()["detalle"] == "breve"
    assert cliente.get("/api/preferencias/T2").json()["tono"] == "calido"      # cada quien la suya (T2 trae sembrado el trato cálido)


def test_preferencias_invalidas_dan_422(cliente):
    assert cliente.put("/api/preferencias/T1", json={"tono": "sarcastico"}).status_code == 422
    assert cliente.put("/api/preferencias/X", json={}).status_code == 404


def test_la_adaptacion_cambia_el_texto_pero_nunca_el_nivel_ni_la_prioridad(cliente):
    base = cliente.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88}).json()
    cliente.put("/api/preferencias/T2", json={"tono": "calido", "detalle": "breve", "recordatorios": "frecuente"})
    adaptada = cliente.post("/api/lecturas", json={"tripulante_id": "T2", "indicador": "spo2", "valor": 88}).json()
    assert base["nivel"] == adaptada["nivel"] == "rojo" and base["prioridad"] == adaptada["prioridad"] == 1
    assert base["acciones_sugeridas"] != adaptada["acciones_sugeridas"]
    assert adaptada["estilo"] == {"tono": "calido", "detalle": "breve", "recordatorios": "frecuente"}
    assert adaptada["proxima_captura_min"] == base["proxima_captura_min"] / 2


def test_el_estado_tambien_usa_el_estilo_elegido(cliente):
    cliente.put("/api/preferencias/T1", json={"tono": "calido", "detalle": "completo", "recordatorios": "normal"})
    e = cliente.get("/api/estado/T1").json()
    assert e["estilo"]["tono"] == "calido" and "Te sugiero volver a medir" in e["acciones_sugeridas"][-1]


def test_con_autenticacion_las_preferencias_son_personales(cliente_auth):
    c = cliente_auth
    h3 = c.entrar("T3")
    assert c.put("/api/preferencias/T3", json={"tono": "calido", "detalle": "breve", "recordatorios": "normal"}, headers=h3).status_code == 200
    for otro in ("T1", "T2", "T4"):
        assert c.get("/api/preferencias/T3", headers=c.entrar(otro)).status_code == 403
        assert c.put("/api/preferencias/T3", json={"tono": "directo"}, headers=c.entrar(otro)).status_code == 403


def test_el_asistente_se_adapta_a_quien_mira_cuando_un_companero_registra(cliente_auth):
    c = cliente_auth
    h3, h1 = c.entrar("T3"), c.entrar("T1")
    c.put("/api/preferencias/T3", json={"tono": "calido", "detalle": "breve", "recordatorios": "normal"}, headers=h3)
    r = c.post("/api/lecturas", json={"tripulante_id": "T1", "indicador": "spo2", "valor": 88}, headers=h3).json()
    assert r["estilo"]["tono"] == "calido"        # T3 registra por T1 y ve el texto con SU estilo
    assert c.get("/api/estado/T1", headers=h1).json()["estilo"]["tono"] == "directo"


def test_las_preferencias_no_guardan_nada_del_diario_ni_del_animo(cliente):
    cliente.post("/api/diario", json={"tripulante_id": "T1", "contenido": "me siento muy mal hoy"})
    cliente.post("/api/animo", json={"tripulante_id": "T1", "valor": 1})
    assert cliente.get("/api/preferencias/T1").json() == {"tono": "directo", "detalle": "completo", "recordatorios": "normal"}
