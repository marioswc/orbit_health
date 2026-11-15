from app.servicios import diagnostico, recursos

MEMINFO = """MemTotal:        7303680 kB
MemFree:          174080 kB
MemAvailable:    1925120 kB
SwapTotal:       7845888 kB
SwapFree:        2531328 kB
"""

CPUINFO = "\n".join(f"processor\t: {i}\nphysical id\t: 0\ncore id\t\t: {i % 4}\n" for i in range(8))


def test_interpreta_proc_meminfo():
    m = recursos.leer_meminfo(MEMINFO)
    assert m["MemAvailable"] == 1925120 and m["SwapTotal"] - m["SwapFree"] == 5314560


def test_cuenta_nucleos_fisicos_y_no_hilos_en_un_procesador_con_smt():
    assert recursos.contar_nucleos_linux(CPUINFO) == 4            # 8 hilos lógicos, 4 núcleos físicos (como el Ryzen 5 7520U)


def test_sin_informacion_en_cpuinfo_devuelve_none():
    assert recursos.contar_nucleos_linux("model name : x\n") is None


def test_los_nucleos_fisicos_nunca_superan_los_logicos_ni_bajan_de_uno():
    n = recursos.nucleos_fisicos()
    assert 1 <= n <= (recursos.os.cpu_count() or 1)


def test_la_memoria_del_equipo_real_tiene_sentido():
    m = recursos.memoria()
    assert m["total_mb"] and m["total_mb"] > 256 and m["disponible_mb"] <= m["total_mb"]


def test_avisa_de_poca_ram_libre_solo_si_se_usa_un_modelo_grande():
    pocos = {"disponible_mb": 900, "swap_usado_mb": 0, "swap_total_mb": 0}
    assert any(t == "memoria" and "900 MB" in d for t, d, _ in recursos.advertencias(pocos, usa_modelo_grande=True))
    assert recursos.advertencias(pocos, usa_modelo_grande=False) == []


def test_avisa_de_swap_alto_como_causa_probable_de_lentitud():
    r = {"disponible_mb": 4000, "swap_usado_mb": 5000, "swap_total_mb": 7000}
    adv = recursos.advertencias(r, usa_modelo_grande=False)
    assert adv and "swap" in adv[0][1] and "lent" in adv[0][2]
    assert recursos.advertencias({"disponible_mb": 4000, "swap_usado_mb": 300, "swap_total_mb": 7000}, False) == []


def test_el_diagnostico_incluye_los_recursos_y_sus_avisos(monkeypatch):
    monkeypatch.setattr(recursos, "memoria", lambda: {"total_mb": 7000, "disponible_mb": 800, "swap_total_mb": 7000, "swap_usado_mb": 6000})
    d = diagnostico.reunir()
    assert d["recursos"]["disponible_mb"] == 800
    assert sum(1 for a in d["advertencias"] if a["tema"] == "memoria") >= 1
