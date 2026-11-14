import sqlite3
import time

import pytest

from app import config
from app.dominio import reglas
from app.dominio.catalogos import validar
from app.fuentes import guion_vivo as g

ORDEN = {"verde": 0, "amarillo": 1, "rojo": 2}


def niveles_en(minuto, tick=0, semilla=7):
    m = g.muestras_en(minuto, tick, semilla)
    por = {t: {s: v for tt, s, v in m if tt == t} for t in g.TRIPULANTES}
    co2 = next(v for _, s, v in m if s == "co2")
    return {t: reglas.evaluar_news2({**por[t], "avpu": "A"}) for t in g.TRIPULANTES}, co2


# ---------- el guion (puro, sin esperar) ----------
def test_el_guion_es_repetible_y_la_semilla_cambia_el_ruido():
    assert g.muestras_en(10, 3, 7) == g.muestras_en(10, 3, 7)
    assert g.muestras_en(10, 3, 7) != g.muestras_en(10, 3, 8)


def test_cada_instante_trae_5_signos_por_tripulante_mas_el_co2_y_todos_son_validos():
    m = g.muestras_en(18, 5, 7)
    assert len(m) == 4 * 5 + 1
    assert all(validar(ind, v) is None for _, ind, v in m)
    assert sum(1 for t, i, _ in m if i == "co2") == 1


def test_al_empezar_todos_estan_en_verde_y_con_pulso_propio():
    niv, co2 = niveles_en(0)
    assert all(r.nivel == "verde" and r.puntos == 0 for r in niv.values()) and co2 < 3.0
    pulsos = {t: next(v for tt, s, v in g.muestras_en(0, 0, 7) if tt == t and s == "frecuencia_cardiaca") for t in g.TRIPULANTES}
    assert len(set(pulsos.values())) > 1                              # nadie tiene el mismo pulso


def test_la_historia_ocurre_como_se_narra():
    niv20, _ = niveles_en(20)
    assert niv20["T1"].nivel == "rojo" and niv20["T1"].puntos >= 7                          # T1 llega a su punto crítico
    niv18, co2_18 = niveles_en(18)
    assert niv18["T2"].nivel == "amarillo" and co2_18 > 3.0                                 # T2 afectado con CO2 alto
    assert niveles_en(32)[0]["T1"].nivel == "verde" and niveles_en(32)[1] < 3.0             # todos se recuperan


def test_ningun_signo_de_t2_es_extremo_por_si_solo():
    """T2 se ve afectado de forma leve: sin extremos que pasen de inmediato, solo el cuadro conjunto."""
    for tick in range(0, 140):
        niv, _ = niveles_en(tick / 4, tick)
        assert not niv["T2"].extremos, tick


def test_t3_y_t4_nunca_se_salen_de_verde():
    for tick in range(0, 140):
        niv, _ = niveles_en(tick / 4, tick)
        assert niv["T3"].nivel == niv["T4"].nivel == "verde", tick


def test_con_las_reglas_estandar_solas_la_alerta_colectiva_cae_dentro_del_apagon_del_enlace():
    activos = []
    for tick in range(0, int(g.DURACION_MIN * 4)):
        minuto = tick / 4
        niv, co2 = niveles_en(minuto, tick)
        if sum(1 for r in niv.values() if ORDEN[r.nivel] >= 1) >= 2 and co2 > 3.0:
            activos.append(minuto)
    assert activos and min(activos) >= 14 and max(activos) <= 22          # eclipse del 14 al 22
    assert [(e[0], e[1]) for e in g.EVENTOS_ENLACE] == [(0.0, True), (14.0, False), (22.0, True)]


def test_los_cambios_de_enlace_se_detectan_una_sola_vez_entre_ticks():
    assert [e[0] for e in g.eventos_enlace_entre(-1, 0)] == [0.0]
    assert [e[0] for e in g.eventos_enlace_entre(10, 20)] == [14.0]
    assert g.eventos_enlace_entre(14, 14.5) == []                             # el límite inferior no se repite


# ---------- el motor, con la API (ritmo alto para que dure segundos) ----------
def esperar_fin(cliente, limite=40):
    fin = time.time() + limite
    while time.time() < fin:
        e = cliente.get("/api/demo/simulacion/estado").json()
        if not e["activa"]:
            return e
        time.sleep(0.05)
    pytest.fail("la simulación no terminó a tiempo")


def test_una_mision_completa_se_ejecuta_sola_y_cuenta_la_historia(cliente):
    r = cliente.post("/api/demo/simulacion/iniciar?ritmo=20&tick_s=0.01")     # 20 s de misión por tick: cabe en la ventana de 60 s
    assert r.status_code == 200 and r.json()["activa"] is True and r.json()["aviso"] is None
    e = esperar_fin(cliente)
    assert e["error"] is None and e["finalizada"] is True and e["progreso_pct"] == 100.0
    assert all(ev["ocurrido"] for ev in e["eventos"])
    h = e["hitos"]
    assert h["primer_rojo"]["tripulante"] == "T1"
    assert h["alerta_colectiva"]["afectados"] >= 2
    assert 10 <= h["alerta_colectiva"]["minuto"] <= 17                          # la línea base se adelanta a las reglas estándar
    assert h["max_retenidos_a_bordo"] > 0                                      # durante el apagón se retuvo lo urgente
    conn = sqlite3.connect(config.DB_PATH)
    origenes = {f[0] for f in conn.execute("SELECT DISTINCT origen FROM lecturas")}
    cola_p1 = conn.execute("SELECT COUNT(*) FROM cola_salida WHERE prioridad=1").fetchone()[0]
    retenidos = conn.execute("SELECT COUNT(*) FROM cola_salida WHERE estado='retenido'").fetchone()[0]
    ind = {f[0] for f in conn.execute("SELECT DISTINCT indicador FROM lecturas")}
    conn.close()
    assert origenes == {"sensor"}                                              # todo entró por el canal de sensores
    assert cola_p1 > 0 and retenidos == 0                                      # lo urgente salió al volver el enlace
    assert {"sueno_horas", "ejercicio_min", "co2", "spo2"} <= ind
    assert cliente.get("/api/enlace").json()["activo"] is True                  # el enlace queda normal
    assert cliente.get("/api/cola/verificar").json()["valida"] is True


def test_al_terminar_no_quedan_ventanas_ni_horas_simuladas_en_memoria(cliente):
    from app.servicios import flujo
    cliente.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01")
    esperar_fin(cliente)
    assert flujo._ventanas == {} and flujo._ultimo_extremo == {}               # una hora "del futuro" no bloquea extremos reales
    r = cliente.post("/api/sensores/flujo", json={"tripulante_id": "T3", "indicador": "spo2", "valor": 86}).json()
    assert r["registrada"] and r["motivo"] == "extremo"                        # un extremo real pasa de inmediato


def test_no_se_pueden_iniciar_dos_a_la_vez_y_se_puede_detener(cliente):
    assert cliente.post("/api/demo/simulacion/iniciar?ritmo=15&tick_s=0.2").status_code == 200
    assert cliente.post("/api/demo/simulacion/iniciar?ritmo=15&tick_s=0.2").status_code == 409
    e = cliente.post("/api/demo/simulacion/detener").json()
    assert e["activa"] is False and e["finalizada"] is False
    assert cliente.get("/api/enlace").json()["activo"] is True                  # detener devuelve el enlace a la normalidad
    assert cliente.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01").status_code == 200   # y se puede volver a empezar
    esperar_fin(cliente)


@pytest.mark.parametrize("consulta", ["ritmo=0", "ritmo=99999", "tick_s=0", "tick_s=60", "guion=inexistente"])
def test_parametros_invalidos(cliente, consulta):
    assert cliente.post(f"/api/demo/simulacion/iniciar?{consulta}").status_code == 422


def test_con_autenticacion_la_simulacion_exige_rol(cliente_auth):
    c = cliente_auth
    assert c.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01").status_code == 401
    assert c.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01", headers=c.entrar("T3")).status_code == 403
    assert c.get("/api/demo/simulacion/estado", headers=c.entrar("T3")).status_code == 403
    assert c.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01", headers=c.entrar("T2")).status_code == 200
    esperar_fin_auth = time.time() + 40
    while time.time() < esperar_fin_auth:
        if not c.get("/api/demo/simulacion/estado", headers=c.entrar("T2")).json()["activa"]:
            break
        time.sleep(0.05)


def test_un_ritmo_mayor_que_la_ventana_de_sensores_avisa_en_vez_de_perder_picos_en_silencio(cliente):
    r = cliente.post("/api/demo/simulacion/iniciar?ritmo=300&tick_s=0.01").json()
    assert r["aviso"] and "mayor que la ventana" in r["aviso"]
    esperar_fin(cliente)
