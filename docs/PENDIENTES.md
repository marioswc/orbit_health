# Estado y pendientes

Última revisión: sábado 14/11/2026, con `main` en la versión que une backend y frontend. Cierre del envío: **domingo 15/11, 11:59 p. m.** hora del evento local.

## Estado verificado

| Qué | Resultado |
|---|---|
| Pruebas del backend | 244 en verde |
| Pruebas del frontend | 93 en verde |
| E2E del backend (`scripts/verificar_e2e.sh`) | OK |
| Compilación del frontend (`npm run build`) | OK, sin recursos remotos (sin CDN ni fuentes externas) |
| Servidor real sirviendo el frontend compilado | `GET /` responde, los 3 recursos del `index` cargan, **24 GET y 5 escrituras que usa la interfaz responden 200** |
| Ramas | `frontend-santi` y `dev-frontend` ya están dentro de `main`; sin conflictos pendientes |
| Marcas de conflicto en `main` | 0 |

## Qué usa ya la interfaz y qué no

| Ya lo usa | Todavía no lo usa |
|---|---|
| lecturas, estado, historial, explicaciones, peligros, preferencias, latencia del enlace, escenarios, diario, tamizajes, **ánimo diario, comparativa con y sin ORBIT, alertas colectivas, acceso con PIN** | `recordatorios`, `tierra/mensajes`, `informe`, `sensores` y `demo/sensor`, `salud` |

## Pendientes, por prioridad

| # | Qué | Quién | Nota |
|---|---|---|---|
| 1 | Completar `docs/SI_DISCLOSURE.md` (dos puntos marcados) y registrarlo en el formulario | Equipo | Regla obligatoria del reto |
| 2 | Demo en inglés: video de 30 s o menos, o 7 diapositivas, en enlace público | Equipo | Si el video es en español, con subtítulos en inglés |
| 3 | Ensayar el demo completo **con el Wi-Fi apagado** en el equipo de la presentación | Equipo | Correr antes `scripts/verificar_e2e.sh` |
| 4 | Mostrar en pantalla lo que falta: recordatorios, vista de Tierra, informe exportable y el sensor simulado | Frontend | Opcional, pero son los que más diferencian |
| 5 | Validación médica de los umbrales | Médico | Es lo más expuesto frente al criterio de Validez |
| 6 | Protocolo si un PHQ-2 sale positivo | Equipo con un profesional | Hoy solo ofrece cápsulas |

## No verificado (hay que comprobarlo a mano)
- Cómo se ve y se siente la interfaz en el navegador, y el flujo completo con una persona usándola.
- El video, las diapositivas y el formulario de envío.
- Que todos los integrantes estén confirmados en el mismo evento local.
- Con `ORBIT_AUTH=1`, el flujo completo de acceso en la interfaz (las pruebas del backend sí lo cubren).

## Cifras que muestra la interfaz
- **Pérdida ósea de 1 a 1.5 % por mes:** verificada en las páginas oficiales de NASA sobre [campos de gravedad](https://www.nasa.gov/hrp/hazard-gravity-fields/) y [cambios óseos](https://www.nasa.gov/reference/risk-of-spaceflight-induced-bone-changes/). La fuente la da para misiones de 4 a 6 meses y avisa de que en más tiempo no está bien caracterizada; la interfaz limita el cálculo a 6 meses y lo marca como ilustrativo.

## Decisiones abiertas
- **Cómo contar la "IA personalizada":** como personalización por preferencias elegidas por el tripulante, sin vender un modelo que aprende personalidades.
- **Menciones a NASA/HRP en el código y los documentos del frontend:** el reto invita a usar esos recursos y pide explicar cómo se usaron, así que no es un problema por sí mismo.

## Si sobra tiempo en el backend
Tierra que responde con retraso, pérdida de paquetes con reintentos y resumir lo rutinario al enviar.

## Fuera de alcance, declarado como trabajo futuro
Cifrado de la base, TLS en la red de la cabina, sensores y radio reales, y un modelo de lenguaje local.
