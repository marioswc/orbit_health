from datetime import datetime, timedelta, timezone

import pytest

from app import config
from app.repositorios import conexion as db
from app.servicios import auditoria, auth

AHORA = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PBKDF2_ITER", 1000)
    ruta = str(tmp_path / "a.db")
    db.init_db(ruta)
    c = db.get_conn(ruta)
    for tid in ("T1", "T2", "T3"):
        c.execute("INSERT INTO tripulantes (id,nombre,rol,fecha_nacimiento) VALUES (?,?,?,?)", (tid, tid, "r", "1990-01-01"))
    c.commit()
    yield c
    c.close()


def test_inscribir_devuelve_pin_y_codigo_una_vez_y_no_guarda_texto_plano(conn):
    r = auth.inscribir(conn, "T1", "comandante")
    assert len(r["pin"]) == 6 and r["codigo_recuperacion"].count("-") == 2
    fila = conn.execute("SELECT * FROM credenciales WHERE tripulante_id='T1'").fetchone()
    assert r["pin"] not in dict(fila).values() and r["codigo_recuperacion"] not in dict(fila).values()


def test_inscribir_valida_datos(conn):
    with pytest.raises(ValueError):
        auth.inscribir(conn, "X", "tripulante")
    with pytest.raises(ValueError):
        auth.inscribir(conn, "T1", "capitan")
    with pytest.raises(ValueError):
        auth.inscribir(conn, "T1", "tripulante", pin="123")
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    with pytest.raises(ValueError):
        auth.inscribir(conn, "T1", "tripulante", pin="123456")


def test_login_correcto_crea_sesion_y_se_valida(conn):
    auth.inscribir(conn, "T1", "comandante", pin="123456")
    s = auth.login(conn, "T1", "123456", AHORA)
    assert auth.sesion(conn, s["token"], AHORA) == {"tripulante_id": "T1", "rol": "comandante"}
    assert auth.sesion(conn, "token-falso", AHORA) is None
    assert auth.sesion(conn, None) is None


def test_sesion_expira_y_se_revoca(conn):
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    s = auth.login(conn, "T1", "123456", AHORA)
    assert auth.sesion(conn, s["token"], AHORA + timedelta(hours=11)) is not None
    assert auth.sesion(conn, s["token"], AHORA + timedelta(hours=13)) is None
    s2 = auth.login(conn, "T1", "123456", AHORA)
    auth.logout(conn, s2["token"], "T1")
    assert auth.sesion(conn, s2["token"], AHORA) is None


def test_pin_incorrecto_y_usuario_inexistente_dan_el_mismo_error(conn):
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    for tid, pin in (("T1", "000000"), ("T9", "123456")):
        with pytest.raises(auth.AuthError) as e:
            auth.login(conn, tid, pin, AHORA)
        assert e.value.codigo == "credenciales" and str(e.value) == "Tripulante o PIN incorrectos"


def test_bloqueo_temporal_y_se_libera_solo(conn, monkeypatch):
    monkeypatch.setattr(config, "MAX_INTENTOS", 3)
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    for _ in range(3):
        with pytest.raises(auth.AuthError):
            auth.login(conn, "T1", "000000", AHORA)
    with pytest.raises(auth.AuthError) as e:
        auth.login(conn, "T1", "123456", AHORA + timedelta(minutes=1))   # ni el PIN correcto entra bloqueado
    assert e.value.codigo == "bloqueado" and e.value.hasta
    assert auth.login(conn, "T1", "123456", AHORA + timedelta(minutes=6))["token"]   # se libera solo


def test_recuperacion_con_codigo_cambia_pin_y_rota_el_codigo(conn):
    r = auth.inscribir(conn, "T1", "tripulante", pin="123456")
    s = auth.login(conn, "T1", "123456", AHORA)
    nuevo = auth.recuperar(conn, "T1", r["codigo_recuperacion"].lower(), "654321", AHORA)
    assert nuevo["codigo_recuperacion"] != r["codigo_recuperacion"]
    assert auth.sesion(conn, s["token"], AHORA) is None                  # sesiones anteriores revocadas
    assert auth.login(conn, "T1", "654321", AHORA)["token"]
    with pytest.raises(auth.AuthError):
        auth.login(conn, "T1", "123456", AHORA)
    with pytest.raises(auth.AuthError):                                  # el código viejo ya no sirve
        auth.recuperar(conn, "T1", r["codigo_recuperacion"], "111111", AHORA)


def test_el_comandante_reinicia_pin_de_otro_y_un_tripulante_no(conn):
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    auth.inscribir(conn, "T2", "comandante", pin="222222")
    auth.inscribir(conn, "T3", "tripulante", pin="333333")
    with pytest.raises(auth.AuthError) as e:
        auth.reiniciar_pin(conn, {"tripulante_id": "T3", "rol": "tripulante"}, "T1")
    assert e.value.codigo == "permiso"
    r = auth.reiniciar_pin(conn, {"tripulante_id": "T2", "rol": "comandante"}, "T1")
    assert auth.login(conn, "T1", r["pin_temporal"], AHORA)["rol"] == "tripulante"


def test_auditoria_registra_y_su_cadena_es_verificable(conn):
    auth.inscribir(conn, "T1", "tripulante", pin="123456")
    auth.login(conn, "T1", "123456", AHORA)
    with pytest.raises(auth.AuthError):
        auth.login(conn, "T1", "000000", AHORA)
    acciones = [a["accion"] for a in auditoria.recientes(conn)]
    assert {"inscripcion", "login", "login_fallido"} <= set(acciones)
    assert auditoria.verificar(conn)["valida"] is True
    conn.execute("UPDATE auditoria SET tipo_evento='login' WHERE tipo_evento='login_fallido'")
    conn.commit()
    assert auditoria.verificar(conn)["valida"] is False                  # manipular el registro se detecta


def test_solo_puede_haber_un_comandante(conn):
    auth.inscribir(conn, "T1", "comandante", pin="111111")
    with pytest.raises(ValueError, match="solo puede haber uno"):
        auth.inscribir(conn, "T2", "comandante", pin="222222")
    assert auth.inscribir(conn, "T2", "tripulante", pin="222222")["rol"] == "tripulante"
