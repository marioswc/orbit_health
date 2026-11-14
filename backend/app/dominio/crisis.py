"""Protocolo determinista de crisis psicológica, riesgo de autolesión y seguimiento de tamizaje (PHQ-2),
integrando la variable de calidad de oxígeno en cabina (`o2_cabina` / `calidad_oxigeno`).

Reglas de diseño:
- Es orientación procedimental a bordo (acompañamiento, entorno seguro, verificación de oxígeno en cabina,
  contención y aviso consentido al médico).
- En un hábitat espacial cerrado, la hipoxia o alteración de O2 ambiental produce síntomas neuroconductuales
  agudos (ansiedad severa, confusión, disforia, alteración del juicio) que pueden desencadenar o agravar una
  crisis psicológica; por ello el protocolo evalúa e incorpora la calidad de oxígeno.
- Nunca emite diagnósticos clínicos ni prescripciones farmacológicas.
- Nunca encola eventos hacia Tierra (`cola_salida`): la privacidad de salud mental en la nave se mantiene intacta.
- Los pasos de seguridad ante crisis son siempre esenciales: no se recortan aunque el tripulante elija detalle 'breve'.
- Supuesto de diseño pendiente de validación por un especialista en salud mental y medicina aeroespacial.
"""
from __future__ import annotations

from .acciones import TONOS
from .catalogos import validar as validar_indicador
from .reglas import evaluar_o2_cabina
from .umbrales import UMBRALES

CORTE_PHQ2 = 3  # Supuesto: tamizaje positivo con total >= 3 (validar con especialista en salud mental)
NIVELES_PROTOCOLO = ("ninguno", "seguimiento", "crisis")
TIPOS_AVISO = ("crisis", "tamizaje_positivo")
ESTADO_VALIDACION = "pendiente_validacion_salud_mental"
AVISO_PROTOCOLO = (
    "Protocolo de apoyo procedimental a bordo (supuesto de diseño pendiente de validación por un especialista "
    "en salud mental). Es orientación de seguridad, no diagnóstico ni indicación de tratamiento."
)

PASO_OXIGENO = {
    "directo": (
        "Verifica de inmediato la calidad de oxígeno en cabina (O₂: {valor} %, nivel {nivel}) y mide tu SpO₂: "
        "la hipoxia o alteración atmosférica en un hábitat cerrado puede causar o agravar agitación, confusión y crisis aguda."
    ),
    "calido": (
        "Revisa primero la calidad de oxígeno en cabina (O₂: {valor} %, nivel {nivel}) y tu SpO₂: cuando el aire "
        "de la nave se altera, el cuerpo puede sentir angustia o confusión que intensifican la crisis."
    ),
}

PASOS_CRISIS = (
    {
        "directo": "No permanezcas a solas: acude ahora a un módulo común o llama por el intercomunicador al médico de a bordo o a un compañero de confianza.",
        "calido": "No tienes que pasar por esto a solas: sal ahora a un módulo común o llama por el intercomunicador al médico de a bordo o a un compañero de confianza.",
    },
    {
        "directo": "Asegura tu entorno inmediato en cabina: aléjate de herramientas, medicamentos o equipos que puedan usarse para hacerte daño.",
        "calido": "Cuida tu entorno inmediato en cabina: mantente en un espacio seguro y lejos de herramientas, medicamentos o equipos con los que puedas lastimarte.",
    },
    {
        "directo": "Aplica contención inmediata: realiza respiración controlada (inhala 4 s, exhala 6 s) y el ejercicio de anclaje sensorial 5-4-3-2-1 mientras llega apoyo.",
        "calido": "Haz una pausa para estabilizarte: respira despacio (inhala 4 s, exhala 6 s) y usa el ejercicio de anclaje 5-4-3-2-1 mientras llega tu compañero.",
    },
    {
        "directo": "Solicita acompañamiento médico a bordo: con tu confirmación puedes enviar un aviso prioritario al médico de la tripulación sin exponer tu diario ni transmitir nada a Tierra.",
        "calido": "Pide acompañamiento médico a bordo: si lo autorizas, enviaremos un aviso prioritario al médico de la tripulación, manteniendo tu diario privado y sin enviar nada a Tierra.",
    },
)

PASOS_SEGUIMIENTO = (
    {
        "directo": "Este resultado es un tamizaje orientativo, no un diagnóstico clínico. Revisa las cápsulas de autorregulación y descanso.",
        "calido": "Recuerda que este resultado es un tamizaje orientativo, no un diagnóstico. Tómate un momento para revisar las cápsulas de autorregulación y descanso.",
    },
    {
        "directo": "Si estás de acuerdo, puedes compartir este resultado positivo con el médico de a bordo mediante consentimiento explícito para programar una conversación privada.",
        "calido": "Si te sientes cómodo, puedes compartir este resultado positivo con el médico de a bordo con tu consentimiento explícito para conversar en privado.",
    },
    {
        "directo": "Si en algún momento aparece crisis aguda o riesgo de hacerte daño, activa de inmediato el protocolo de crisis psicológica.",
        "calido": "Si en algún momento sientes que entras en crisis o que no estás a salvo, activa de inmediato el protocolo de crisis psicológica.",
    },
)


def evaluar_calidad_oxigeno(calidad_oxigeno: float | None = None) -> dict:
    """Clasifica la calidad de oxígeno en cabina (% O2) y detecta si puede contribuir a síntomas neuroconductuales."""
    if calidad_oxigeno is None:
        return {"presente": False, "valor_pct": None, "nivel": None, "alerta": False, "causa": None}
    val = float(calidad_oxigeno)
    err = validar_indicador("o2_cabina", val)
    if err:
        raise ValueError(err)
    nivel = evaluar_o2_cabina(val)
    o = UMBRALES["ambiente"]["o2_pct"]
    if val < o["amarillo_bajo"]:
        causa = "hipoxia_ambiental"
    elif val > o["amarillo_alto"]:
        causa = "hiperoxia_riesgo_incendio"
    else:
        causa = "nominal"
    return {
        "presente": True,
        "valor_pct": round(val, 2),
        "nivel": nivel,
        "alerta": nivel != "verde",
        "causa": causa,
    }


def evaluar_tamizaje(item1: int, item2: int, riesgo_autolesion: bool = False,
                     calidad_oxigeno: float | None = None) -> dict:
    """Evalúa el PHQ-2 junto con la pregunta de riesgo de autolesión/crisis y la calidad de oxígeno en cabina."""
    if not (0 <= int(item1) <= 3 and 0 <= int(item2) <= 3):
        raise ValueError("Cada ítem del PHQ-2 debe estar entre 0 y 3")
    total = int(item1) + int(item2)
    riesgo = bool(riesgo_autolesion)
    o2 = evaluar_calidad_oxigeno(calidad_oxigeno)

    if riesgo or o2["nivel"] == "rojo":
        nivel = "crisis"
        categorias = ("crisis", "autorregulacion")
    elif total >= CORTE_PHQ2 or o2["nivel"] == "amarillo":
        nivel = "seguimiento"
        categorias = ("autorregulacion",)
    else:
        nivel = "ninguno"
        categorias = ()
    return {
        "total": total,
        "positivo": total >= CORTE_PHQ2 or riesgo or o2["alerta"],
        "riesgo_autolesion": riesgo,
        "calidad_oxigeno": o2,
        "nivel_protocolo": nivel,
        "categorias_capsulas": categorias,
    }


def protocolo_crisis(nivel: str = "crisis", tono: str = "directo",
                     calidad_oxigeno: float | None = None) -> dict:
    """Devuelve el protocolo estructurado según el nivel, el tono elegido y la calidad de oxígeno en cabina."""
    if nivel not in NIVELES_PROTOCOLO:
        raise ValueError(f"nivel de protocolo debe ser uno de: {', '.join(NIVELES_PROTOCOLO)}")
    tono_efectivo = tono if tono in TONOS else "directo"
    o2 = evaluar_calidad_oxigeno(calidad_oxigeno)

    if nivel == "crisis":
        titulo = "Protocolo de crisis psicológica y seguridad a bordo"
        urgencia = "inmediata"
        pasos = [p[tono_efectivo] for p in PASOS_CRISIS]
        contactos = [
            {"rol": "medico", "etiqueta": "Médico de a bordo (contacto prioritario)"},
            {"rol": "comandante", "etiqueta": "Comandante / compañero de guardia en cabina"},
        ]
        permite_aviso = True
    elif nivel == "seguimiento":
        titulo = "Seguimiento sugerido tras tamizaje positivo"
        urgencia = "preventiva"
        pasos = [p[tono_efectivo] for p in PASOS_SEGUIMIENTO]
        contactos = [{"rol": "medico", "etiqueta": "Médico de a bordo"}]
        permite_aviso = True
    else:
        titulo = "Sin señales de alerta en el tamizaje"
        urgencia = "ninguna"
        pasos = []
        contactos = []
        permite_aviso = False

    if o2["alerta"]:
        paso_o2 = PASO_OXIGENO[tono_efectivo].format(valor=o2["valor_pct"], nivel=o2["nivel"])
        pasos = [paso_o2, *pasos]

    return {
        "nivel": nivel,
        "titulo": titulo,
        "urgencia": urgencia,
        "tono": tono_efectivo,
        "pasos": pasos,
        "calidad_oxigeno": o2,
        "contactos_abordo": contactos,
        "permite_aviso_medico": permite_aviso,
        "privado": True,
        "transmitido_tierra": False,
        "estado_validacion": ESTADO_VALIDACION,
        "aviso": AVISO_PROTOCOLO,
    }
