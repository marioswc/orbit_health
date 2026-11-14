#!/usr/bin/env python3
"""Genera docs/casos_validacion.csv: escenarios con la salida actual del motor y columnas vacías
para que un clínico anote su nivel esperado. Los escenarios son hipotéticos, no datos de personas."""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
from app import engine  # noqa: E402

BASE = dict(frecuencia_respiratoria=16, spo2=98, presion_sistolica=120,
            frecuencia_cardiaca=70, avpu="A", temperatura=36.8)
CASOS = [
    ("Todo normal", {}),
    ("Hipoxia severa aislada", {"spo2": 88}),
    ("Hipoxia leve aislada", {"spo2": 94}),
    ("Fiebre aislada", {"temperatura": 39.5}),
    ("Hipotermia aislada", {"temperatura": 34.8}),
    ("Taquicardia moderada aislada", {"frecuencia_cardiaca": 125}),
    ("Bradicardia severa aislada", {"frecuencia_cardiaca": 38}),
    ("Taquipnea severa aislada", {"frecuencia_respiratoria": 27}),
    ("Hipotensión severa aislada", {"presion_sistolica": 85}),
    ("Conciencia alterada aislada", {"avpu": "V"}),
    ("Deterioro leve combinado", {"frecuencia_respiratoria": 22, "spo2": 93, "frecuencia_cardiaca": 95, "temperatura": 38.5}),
    ("Deterioro moderado combinado", {"frecuencia_respiratoria": 22, "spo2": 93, "presion_sistolica": 100, "frecuencia_cardiaca": 115, "temperatura": 38.5}),
    ("Sepsis probable (fiebre, taquicardia, taquipnea, hipotensión)", {"temperatura": 39.3, "frecuencia_cardiaca": 128, "frecuencia_respiratoria": 26, "presion_sistolica": 92}),
    ("Frecuencia cardiaca baja en atleta entrenado (posible normal)", {"frecuencia_cardiaca": 48}),
]

with (RAIZ / "docs" / "casos_validacion.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["caso", "FR", "SpO2", "PAS", "FC", "AVPU", "Temp", "puntos_sistema",
                "nivel_sistema_conservador", "nivel_sistema_RCP",
                "nivel_esperado_clinico", "de_acuerdo (si/no)", "comentario_clinico"])
    for nombre, cambios in CASOS:
        s = {**BASE, **cambios}
        engine.MODO_PARAMETRO_EXTREMO = "conservador"
        c = engine.evaluar_news2(s)
        engine.MODO_PARAMETRO_EXTREMO = "rcp"
        r = engine.evaluar_news2(s)
        w.writerow([nombre, s["frecuencia_respiratoria"], s["spo2"], s["presion_sistolica"],
                    s["frecuencia_cardiaca"], s["avpu"], s["temperatura"], c.puntos, c.nivel, r.nivel, "", "", ""])
print("docs/casos_validacion.csv generado")
