# Paquete de validación médica

Objetivo: que un profesional de la salud (idealmente medicina aeroespacial o de urgencias, más un perfil de salud mental) revise y firme cada criterio clínico del prototipo. Hasta entonces, todo lo de este documento es **supuesto de diseño**.

## 1. Cómo revisarlo (flujo propuesto)

| Paso | Qué hace el clínico | Material |
|---|---|---|
| 1 | Revisa los supuestos de la sección 2 y responde aprobar, ajustar o rechazar | Este documento |
| 2 | Marca el nivel esperado de cada escenario | `docs/casos_validacion.csv` (regenerar con `scripts/generar_casos_validacion.py`) |
| 3 | Revisa el flujo de salud mental de la sección 3 | Este documento |
| 4 | Nosotros ajustamos umbrales, corremos pruebas y dejamos constancia (quién, cuándo, versión) | Commit y registro de decisión |

## 2. Inventario de supuestos clínicos

Los valores numéricos viven en `backend/app/datos/umbrales.json`. Para aplicar una decisión clínica basta editar ese archivo (o apuntar a otro con `ORBIT_UMBRALES`); `estado` indica si siguen pendientes de validación y se muestra en la interfaz.

| # | Supuesto | Valor actual | Dónde | Pregunta al clínico | Verificar contra |
|---|---|---|---|---|---|
| 1 | Un parámetro NEWS2 aislado en 3 puntos | Rojo (modo conservador) | `datos/umbrales.json` | ¿Rojo o amarillo, dado que no hay evacuación posible? | Publicación NEWS2 del Royal College of Physicians |
| 2 | Escala de SpO₂ | Escala 1 | `datos/umbrales.json` | NEWS2 prevé una escala 2 para retención de CO₂. Con CO₂ de cabina elevado, ¿aplica? | Publicación NEWS2 |
| 3 | Variables ausentes | Suman 0 | `datos/umbrales.json` | ¿Se debe exigir captura mínima antes de dar nivel verde? | Criterio clínico |
| 4 | Ventana de lecturas vigentes | 60 min | `datos/umbrales.json` | ¿Es razonable para captura manual? | Criterio clínico |
| 5 | Línea base personal | 14 días, ≥5 muestras, >2 DE | `datos/umbrales.json` | ¿Es adecuado en microgravedad, donde hay cambios fisiológicos esperables y no patológicos? ¿Deben variar por indicador? | Literatura de fisiología espacial |
| 6 | Aviso de línea base sube verde a amarillo | Sí | `servicios/lecturas.py` | ¿Genera demasiadas falsas alarmas? | Criterio clínico |
| 7 | CO₂ de cabina | ≤3.0 verde, 3.1–4.0 amarillo, >4.0 rojo (mmHg) | `datos/umbrales.json` | ¿Umbrales y unidades correctos? | Normas de calidad de aire en hábitats cerrados |
| 8 | Dosis acumulada | 70 % amarillo, 90 % rojo del límite de misión | `datos/umbrales.json` | ¿Qué límite de misión se usa y quién lo define? | Estándares de protección radiológica ocupacional |
| 9 | Glucosa capilar | <54 rojo, <70 amarillo, 100–125 observación, ≥126 amarillo, ≥300 rojo (mg/dL) | `datos/umbrales.json` | ¿Umbrales y acciones? | Guías de diabetes vigentes |
| 10 | Presión diastólica | <60 mmHg observación | `datos/umbrales.json` | ¿Útil o ruido? | Criterio clínico |
| 11 | Rangos de captura | Sección `indicadores` de `datos/umbrales.json` | `datos/umbrales.json` | ¿Rechazan valores plausibles o aceptan imposibles? | Criterio clínico |
| 12 | Conciencia (AVPU) | Autocaptura | Frontend | Una persona con conciencia alterada no puede registrarla. ¿Debe capturarla un compañero? | Criterio clínico |
| 13 | Prioridad de cola | Rojo 1, amarillo 2, verde 3 | `servicios/lecturas.py` | ¿El orden de transmisión es el correcto? | Criterio clínico |
| 14 | Regla combinada: pulso >90 con presión sistólica ≤110 | Nivel amarillo | `datos/umbrales.json` (`reglas_combinadas`) | ¿Es útil como aviso? ¿Debe ser rojo? | Criterio clínico |
| 15 | Regla combinada: temperatura ≥38.1 con pulso >90 | Nivel amarillo | `datos/umbrales.json` (`reglas_combinadas`) | ¿Sensibilidad adecuada o genera ruido? | Criterio clínico |
| 16 | Alerta colectiva de CO₂ | CO₂ >3.0 mmHg y ≥2 tripulantes en amarillo o peor, resultado rojo | `datos/umbrales.json` (`colectiva_co2`) | ¿Mínimo de tripulantes y nivel correctos? | Criterio clínico y normas de cabina |

## 3. Salud mental: puntos que requieren decisión humana

El diseño actual protege la privacidad del tripulante: el diario, el PHQ-2 y el ánimo nunca salen de su espacio personal ni de la nave. La única vía hacia otra persona es un aviso que el propio tripulante decide enviar al médico o al comandante, con consentimiento explícito y revocable. Eso es deliberado, pero deja decisiones que no debemos tomar nosotros.

| Tema | Situación actual | Riesgo | Opciones |
|---|---|---|---|
| PHQ-2 positivo (≥3) | Ofrece cápsulas y permite, solo con consentimiento explícito (`POST /api/crisis/aviso-medico`), avisar al médico de a bordo (revocable por el propio tripulante) | Un tamizaje positivo requiere seguimiento; en confinamiento no hay derivación externa | Implementada la opción B (consentimiento explícito y revocable), pendiente de validación por salud mental |
| Riesgo de autolesión o crisis aguda + calidad de O₂ (`o2_cabina` / `calidad_oxigeno`) | Protocolo procedimental de crisis (`GET /api/crisis/protocolo` y `POST /api/tamizajes`) que cruza síntomas agudos con la calidad de oxígeno en cabina (hipoxia/hiperoxia ambiental) y da pasos de acompañamiento y entorno seguro | Los pasos y umbrales de O₂ (19.5–23.0 % nominal) son supuestos procedimentales de diseño | Revisar y firmar el protocolo con especialistas en salud mental y medicina aeroespacial antes de uso real |
| Validez del instrumento | PHQ-2 validado en población terrestre | Su desempeño en misiones prolongadas no está respaldado por este proyecto | Verificar la literatura; declararlo como tamizaje, no diagnóstico |
| Diario | Texto libre, sin cifrar. La autenticación por tripulante existe pero viene apagada por defecto | Con la autenticación apagada, cualquiera con acceso al equipo puede leerlo | Activar la autenticación y cifrar en reposo |
| Contenido de cápsulas | Texto genérico redactado por nosotros | Puede ser inadecuado | Revisión de un psicólogo antes de mostrar |

Estado: la opción B (compartir solo con consentimiento explícito y revocable) ya está implementada junto con un protocolo de apoyo procedimental. Sigue pendiente la validación de un profesional de salud mental.

## 4. IA: dónde sí aporta y dónde no

Principio vigente: la **decisión clínica** sigue siendo determinista y auditable. La IA, si entra, es asesora, corre en local y no cambia niveles de alerta por sí sola.

| Idea | Valor | Riesgo | Veredicto |
|---|---|---|---|
| Explicación en lenguaje natural de por qué salió un nivel (modelo local pequeño) | Ayuda a tripulantes no médicos | Puede alucinar; consume recursos | Viable: generar el texto desde el desglose del motor y no desde el modelo |
| Detección multivariable de anomalías como aviso secundario | Detecta patrones que las reglas no ven | Pocos datos, falsos positivos, opacidad | Posible solo como "aviso a revisar", marcado como experimental |
| Asistente conversacional de apoyo emocional | Compañía en aislamiento | Riesgo clínico alto, sin supervisión | No recomendado sin diseño clínico y evaluación formal |
| Análisis de sentimiento sobre el diario | Detectaría deterioro temprano | Rompe la promesa de privacidad | No hacerlo |
| Resumen del estado para Tierra cuando vuelve el enlace | Ahorra tiempo al equipo en Tierra | Errores de síntesis | Viable con plantilla determinista y verificación de cadena |

## 5. Qué más puede potenciar el proyecto (sin cambiar el principio de autonomía)

| Mejora | Beneficio | Esfuerzo (supuesto) |
|---|---|---|
| Casos dorados firmados por el clínico como pruebas automáticas | Cada cambio de umbral se valida contra criterio médico | Bajo |
| Registro de auditoría de decisiones (quién registró, qué nivel, versión de reglas) | Trazabilidad | Medio |
| Autenticación por tripulante y cifrado en reposo | Cierra la deuda de privacidad | Medio |
| Informe exportable (PDF) para Tierra tras la reconexión | Comunicación útil | Medio |
| Ingesta de sensores con adaptador común | Pasar de captura manual a sensores reales | Alto |
| Escenarios de misión guionizados | Demo reproducible y pruebas de estrés | Bajo |
| Interfaz en español e inglés y accesibilidad | Alcance y uso bajo estrés | Medio |

## 6. Decisiones pendientes del equipo

- Perfil clínico que validará (medicina aeroespacial, urgencias, salud mental) y cómo se documenta su visto bueno.
- Opción A, B o C para el PHQ-2 positivo (sección 3).
- Si algo de la sección 4 entra al alcance de hoy; recomendado: ninguna.
- Aviso de alcance: el sistema es un prototipo de apoyo y no sustituye criterio médico. Cualquier uso real requeriría revisión regulatoria y legal que no se cubre aquí.
