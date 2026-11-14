from datetime import datetime, timedelta, timezone

from app.dominio import seguridad as s

AHORA = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def test_pin_valido():
    assert s.pin_valido("123456") and s.pin_valido("1234567890")
    assert not s.pin_valido("12345") and not s.pin_valido("12a456") and not s.pin_valido("")


def test_generados_cumplen_formato():
    for _ in range(50):
        assert s.pin_valido(s.generar_pin())
    cod = s.generar_codigo_recuperacion()
    assert len(cod) == 14 and cod.count("-") == 2 and cod == cod.upper()


def test_hash_con_sal_propia_y_verificacion():
    sal1, h1 = s.hash_secreto("123456", 1000)
    sal2, h2 = s.hash_secreto("123456", 1000)
    assert sal1 != sal2 and h1 != h2                      # la sal evita hashes iguales
    assert s.verificar_secreto("123456", sal1, h1, 1000)
    assert not s.verificar_secreto("123457", sal1, h1, 1000)
    assert not s.verificar_secreto("123456", sal1, h1, 2000)   # otra iteración no verifica


def test_token_se_guarda_solo_como_hash():
    t = s.nuevo_token()
    assert len(t) >= 40 and s.hash_token(t) != t and s.hash_token(t) == s.hash_token(t)


def test_bloqueo_temporal_y_reinicio_de_cuenta():
    n, hasta = 0, None
    for _ in range(4):
        n, hasta = s.tras_fallo(n, AHORA, 5, 5)
    assert n == 4 and hasta is None
    n, hasta = s.tras_fallo(n, AHORA, 5, 5)
    assert n == 0 and hasta is not None                   # bloqueado y contador reiniciado
    assert s.esta_bloqueado(hasta, AHORA)
    assert not s.esta_bloqueado(hasta, AHORA + timedelta(minutes=6))   # nunca permanente


def test_permisos_por_rol():
    assert s.permitido("tripulante", "clinico:leer") and s.permitido("tripulante", "clinico:escribir")
    assert not s.permitido("tripulante", "enlace:cambiar") and s.permitido("medico", "enlace:cambiar")
    assert not s.permitido("tripulante", "auditoria:leer") and s.permitido("comandante", "auditoria:leer")
    assert not s.permitido("tripulante", "accion_inexistente")
