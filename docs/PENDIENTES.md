# Estado y pendientes

Última revisión: sábado 14/11/2026, después de comprobar el repositorio, las ramas y la compilación. Cierre del envío: **domingo 15/11, 11:59 p. m.** hora del evento local.

## Estado verificado

| Qué | Resultado |
|---|---|
| `main` | 244 pruebas en verde, E2E OK, sin marcas de conflicto |
| Backend | Completo para el reto: clasificación, historial, explicaciones, peligros del HRP, asistente por preferencias, recordatorios, sensores simulados, informe exportable, vista de Tierra y comparativa con y sin ORBIT |
| `frontend-santi` | Compila sin errores (`npm run build` verificado), no carga recursos remotos, se une a `main` sin conflictos |
| `dev-frontend` | Conflicto con `main` **solo** en `frontend/docs/README.md` (dos READMEs distintos de Lourdes y Santiago) |

## Lo que el frontend ya usa y lo que le falta

| Ya lo usa | Todavía no lo usa |
|---|---|
| lecturas, estado, historial, explicaciones, peligros, preferencias, latencia del enlace, escenarios de demo, diario, tamizajes | `animo`, `recordatorios`, `tierra/mensajes`, `informe`, `demo/comparativa`, `demo/sensor`, alertas colectivas y el acceso con PIN (`auth`) cuando esté activado |

## Pendientes, por prioridad

| # | Qué | Quién | Nota |
|---|---|---|---|
| 1 | Completar `docs/SI_DISCLOSURE.md` (dos puntos marcados) y registrarlo en el formulario | Equipo | Regla obligatoria del reto |
| 2 | Decidir cuál rama de frontend es la oficial, unirla a `main` y resolver el README | Santiago y Lourdes | `git pull origin main` antes de unir |
| 3 | Conectar lo que falta en la tabla de arriba, sobre todo la **comparativa con y sin ORBIT** y los **recordatorios** | Frontend | Es lo más visible para el jurado |
| 4 | Demo en inglés: video de 30 s o menos, o 7 diapositivas, en enlace público | Equipo | Si es video en español, con subtítulos en inglés |
| 5 | Ensayar el demo completo con el Wi-Fi apagado en el equipo de la presentación | Equipo | `scripts/verificar_e2e.sh` antes de empezar |
| 6 | Validación médica de los umbrales | Médico | Es lo más expuesto frente al criterio de Validez |
| 7 | Protocolo si un PHQ-2 sale positivo | Equipo con un profesional | Hoy solo ofrece cápsulas |

## No verificado (hay que comprobarlo a mano)
- Cómo se ve la interfaz y si el flujo completo funciona en el navegador contra este backend.
- El video, las diapositivas y el formulario de envío.
- Que todos los integrantes estén confirmados en el mismo evento local.

## Decisiones abiertas
- **Menciones a NASA/HRP en el código del frontend** (8 archivos). El reto invita a usar esos recursos y la guía del demo pide explicar cómo se usaron, así que no es un problema por sí mismo. Conviene que el equipo lo confirme.
- **Cómo contar la "IA personalizada"**: como personalización por preferencias elegidas por el tripulante, sin vender un modelo que aprende personalidades.

## Si sobra tiempo en el backend
Tierra que responde con retraso, pérdida de paquetes con reintentos y resumir lo rutinario al enviar.

## Fuera de alcance, declarado como trabajo futuro
Cifrado de la base, TLS en la red de la cabina, sensores y radio reales, y un modelo de lenguaje local.
