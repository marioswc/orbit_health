from app import config
from app.fuentes import cuentas_demo
from app.repositorios.conexion import get_conn
from app.servicios import auth


def test_las_cuentas_demo_se_crean_una_sola_vez_y_permiten_entrar(cliente, monkeypatch):
    monkeypatch.setattr(config, "PBKDF2_ITER", 1000)
    conn = get_conn()
    try:
        primera = cuentas_demo.crear(conn)
        assert [c[3] for c in primera] == [True, True, True, True]
        segunda = cuentas_demo.crear(conn)                                  # no pisa nada
        assert [c[3] for c in segunda] == [False, False, False, False]
        for tid, rol, pin, _ in primera:
            sesion = auth.login(conn, tid, pin)
            assert sesion["rol"] == rol
        try:
            auth.login(conn, "T1", "000000")
            raise AssertionError("un PIN equivocado no debe entrar")
        except auth.AuthError:
            pass
    finally:
        conn.close()


def test_los_pin_demo_son_validos_para_la_politica_de_pin():
    from app.dominio import seguridad
    assert all(seguridad.pin_valido(pin) for _, _, pin in cuentas_demo.CUENTAS)


def test_en_una_base_vacia_crea_primero_la_tripulacion(tmp_path, monkeypatch):
    from app.repositorios.conexion import get_conn, init_db
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "vacia.db"))
    monkeypatch.setattr(config, "PBKDF2_ITER", 1000)
    init_db()
    conn = get_conn()
    try:
        assert [c[3] for c in cuentas_demo.crear(conn)] == [True, True, True, True]
    finally:
        conn.close()
