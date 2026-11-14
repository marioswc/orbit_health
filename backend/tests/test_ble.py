import pytest

from app.fuentes import ble


def test_frecuencia_en_un_byte():
    assert ble.parsear_medicion_fc(bytes([0x00, 72])) == {"fc": 72, "contacto": None, "rr_ms": []}


def test_frecuencia_en_dos_bytes_little_endian():
    assert ble.parsear_medicion_fc(bytes([0x01, 0x2C, 0x01]))["fc"] == 300      # 0x012C


def test_intervalos_rr_en_unidades_de_un_1024avo_de_segundo():
    m = ble.parsear_medicion_fc(bytes([0x10, 60, 0x00, 0x04, 0x00, 0x02]))      # 1024 y 512 unidades
    assert m["fc"] == 60 and m["rr_ms"] == [1000.0, 500.0]


def test_energia_gastada_se_salta_y_los_rr_siguen_siendo_correctos():
    m = ble.parsear_medicion_fc(bytes([0x18, 80, 0x0A, 0x00, 0x00, 0x04]))
    assert m["fc"] == 80 and m["rr_ms"] == [1000.0]


@pytest.mark.parametrize("banderas,esperado", [(0x00, None), (0x04, False), (0x06, True), (0x02, None)])
def test_estado_de_contacto_con_la_piel(banderas, esperado):
    assert ble.parsear_medicion_fc(bytes([banderas, 70]))["contacto"] is esperado


@pytest.mark.parametrize("paquete", [b"", bytes([0x01, 0x2C]), bytes([0x08, 70, 0x01])])
def test_paquetes_vacios_o_truncados_se_rechazan(paquete):
    with pytest.raises(ValueError):
        ble.parsear_medicion_fc(paquete)


def test_sin_contacto_o_valor_imposible_no_se_envia_nada():
    assert ble.muestra_valida({"fc": 72, "contacto": True, "rr_ms": []}) == 72.0
    assert ble.muestra_valida({"fc": 72, "contacto": None, "rr_ms": []}) == 72.0
    assert ble.muestra_valida({"fc": 72, "contacto": False, "rr_ms": []}) is None      # banda sin tocar la piel
    assert ble.muestra_valida({"fc": 0, "contacto": True, "rr_ms": []}) is None         # lectura vacía habitual al conectar
    assert ble.muestra_valida({"fc": 300, "contacto": True, "rr_ms": []}) is None       # fuera del rango del catálogo


def test_los_identificadores_son_los_estandar_de_bluetooth():
    assert ble.SERVICIO_FC.startswith("0000180d") and ble.CARACTERISTICA_FC.startswith("00002a37")


def test_el_puente_arranca_y_muestra_su_ayuda_sin_necesitar_bluetooth():
    import subprocess
    import sys
    from pathlib import Path
    script = Path(__file__).resolve().parents[2] / "scripts" / "puente_ble.py"
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and "--escanear" in r.stdout and "NO está probado con una banda real" in r.stdout
