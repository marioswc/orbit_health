# Decisiones del equipo (14/11/2026)

> Son **criterio del equipo**, no validación médica. Siguen pendientes de revisión por un médico de urgencias y por un especialista en medicina aeroespacial (ver `VALIDACION_MEDICA.md`).

| # | Tema | Decisión | Estado en el código | Riesgo o nota |
|---|---|---|---|---|
| 1 | Quién valida | Dos perfiles: urgencias (NEWS2 y glucemia) y medicina aeroespacial (cabina, radiación, microgravedad). Sin perfil aeroespacial, esos umbrales se declaran como supuestos de diseño | Sin cambios | Documentar quién firma y cuándo |
| 2 | Un parámetro aislado en 3 puntos | Rojo, prioridad 1. Se declara como adaptación propia para aislamiento | Implementado (`modo_parametro_extremo = conservador`) | Se aparta del esquema RCP; decirlo así en la presentación |
| 3 | Escala de SpO₂ con CO₂ alto | Escala 1 siempre. El CO₂ se evalúa aparte. Si se simulan patologías crónicas, un indicador por tripulante, nunca activado por el sensor ambiental | Implementado (solo escala 1) | El indicador por tripulante no existe aún |
| 4 | Frecuencia de captura | Verde 60 min, amarillo 15 min, rojo 5 min (el equipo habló de 1–5) | Implementado como recomendación (`proxima_captura_min`) | La vigencia de las lecturas sigue fija en 60 min; diferenciarla por nivel queda como opción |
| 5 | Línea base de 14 días | Ventana móvil que absorbe la adaptación a microgravedad, siempre como aviso preventivo y nunca como sustituto de los umbrales absolutos | Implementado (solo sube verde a amarillo) | En los primeros días de vuelo la desviación puede inflarse; una tendencia lenta puede "normalizar" un deterioro |

## Puntos de las respuestas que no coinciden con el código o con lo acordado

| Afirmación | Realidad | Qué hacer |
|---|---|---|
| "Cruzamos las alertas de CO₂ y SpO₂" | **No está implementado.** Hoy se evalúan por separado | No decirlo en la demo, o implementar la correlación primero |
| "Supuestos calibrados con literatura oficial" | Los umbrales son supuestos de diseño que no se han verificado contra fuentes publicadas | Decir "supuestos de diseño basados en NEWS2, pendientes de validación médica" y citar solo fuentes realmente consultadas |
| "Frecuencia dinámica de captura" | Solo recomienda el intervalo; no hay recordatorios ni bloqueo | Presentarlo como recomendación |

## Opciones abiertas

| Opción | Pro | Contra |
|---|---|---|
| Vigencia de lecturas por nivel (60/15/15) | Evita arrastrar puntajes viejos | Más reglas que validar |
| Correlación CO₂ con síntomas de la tripulación | Cumple lo prometido en la demo | Requiere definir qué es "correlación" con un clínico |
| Marcar los primeros N días como adaptación y no emitir avisos de línea base | Menos falsas alarmas al inicio | Puede ocultar un deterioro real; N lo define el clínico |
