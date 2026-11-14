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
| "Cruzamos las alertas de CO₂ y SpO₂" | **Implementado** con `GET /api/alertas/colectivas`: CO₂ sobre 3.0 mmHg y al menos 2 tripulantes con nivel fisiológico amarillo o peor. Las lecturas ambientales no cuentan como afectado | Condiciones y niveles son supuestos; validar con el clínico |
| "Supuestos calibrados con literatura oficial" | Los umbrales son supuestos de diseño que no se han verificado contra fuentes publicadas | Decir "supuestos de diseño basados en NEWS2, pendientes de validación médica" y citar solo fuentes realmente consultadas |
| "Frecuencia dinámica de captura" | Solo recomienda el intervalo; no hay recordatorios ni bloqueo | Presentarlo como recomendación |

## Opciones abiertas

| Opción | Pro | Contra |
|---|---|---|
| Vigencia de lecturas por nivel (60/15/15) | Evita arrastrar puntajes viejos | Más reglas que validar |
| Marcar los primeros N días como adaptación y no emitir avisos de línea base | Menos falsas alarmas al inicio | Puede ocultar un deterioro real; N lo define el clínico |

## Pensado para quien está a bordo (decisiones de diseño, 14/11)

| Necesidad de la tripulación | Qué hace el sistema | Límite |
|---|---|---|
| Nadie puede reparar el sistema | Verifica la base al arrancar, restaura el último respaldo válido y respalda solo; conserva la base dañada como evidencia. `GET /api/salud` informa el estado | Los respaldos viven en el mismo equipo: si falla el disco completo, se pierden |
| Una alerta roja sin instrucciones genera pánico | Cada alerta devuelve `acciones_sugeridas`: repetir la medición, avisar, volver a medir en N min | Son pasos de procedimiento. **No hay indicaciones de tratamiento**; las debe definir un clínico |
| Alguien puede quedar incapacitado | Cualquier tripulante autenticado registra y ve los signos de un compañero | Queda en la auditoría |

## Para el reto (revisado contra las reglas oficiales, 14/11)

| Tema | Decisión | Nota |
|---|---|---|
| Criterio "Relevancia" pide integrar datos de NASA como componente central | Se integró el marco de peligros y riesgos del HRP (`GET /api/peligros`) y cada alerta indica su peligro | La asociación indicador-peligro es de diseño nuestro, no oficial. Cobertura honesta: 1 de 17 riesgos cubierto, 7 parciales, 9 no |
| Uso de IA | Se permite, con declaración obligatoria y sin usarla para idear la solución | Ver `SI_DISCLOSURE.md`; el equipo debe completar los puntos marcados |
| "IA adaptada a la personalidad" | Se implementó como preferencias elegidas por cada tripulante (tono, detalle, recordatorios), un explicador local opcional (`GET /api/estado/{tid}/explicacion`) y voz push-to-talk opcional (`POST /api/voz/chat/{tid}`) | El modelo solo explica o conversa sobre un estado ya calculado; nunca cambia nivel, prioridad ni acciones. No se infiere nada del diario ni del ánimo. Sin modelos configurados se usan fallbacks locales |
| Contenido educativo | `GET /api/explicaciones` por indicador, con fuentes oficiales | Pendiente de validación clínica; sin consejo médico ni de medicación |
| Sueño y ánimo | Indicadores nuevos; el ánimo es privado como el PHQ-2 | Umbrales son supuestos |
