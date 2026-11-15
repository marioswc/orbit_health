# Referencia de la API

> **Generado automáticamente** por `scripts/generar_api_doc.py` a partir del código. No se edita a mano: una prueba
> falla si este archivo no coincide con las rutas reales. Para regenerarlo: `backend/.venv/bin/python scripts/generar_api_doc.py`.

Con `ORBIT_AUTH=1` todas las rutas exigen sesión (`Authorization: Bearer <token>`) **excepto** las marcadas como públicas.
Qué rol puede usar cada una está en [SEGURIDAD_A_BORDO.md](SEGURIDAD_A_BORDO.md).


## sistema

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/entornos` | pública | Entornos de la misión con su gravedad y si la estimación de pérdida ósea aplica en cada uno |
| GET | `/api/entornos/{clave}` | pública | Un entorno de la misión: gravedad y aplicabilidad de la estimación ósea |
| GET | `/api/explicaciones` | pública | Qué es cada medición, por qué se mide, cómo medirla y qué cambia en el espacio |
| GET | `/api/explicaciones/{clave}` | pública | Explicación de un indicador: qué es, por qué se mide y cómo medirlo |
| GET | `/api/health` | pública | Comprobación de que el servidor responde |
| GET | `/api/indicadores` | pública | Catálogo de indicadores con su unidad y rango de captura |
| GET | `/api/peligros` | pública | Marco de peligros y riesgos del HRP, con la cobertura real de ORBIT Health por cada riesgo |
| GET | `/api/salud` | pública | Estado de la base y de los respaldos. Pensado para que un tripulante no técnico sepa si todo está bien |
| GET | `/api/tripulantes` | pública | Lista de tripulantes (id, nombre y rol) para el selector de acceso |
| GET | `/api/umbrales` | pública | Perfil, versión y estado de validación clínica de los umbrales en uso |

## seguridad

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/auditoria` | requerida | Últimos registros de auditoría (solo el comandante) |
| GET | `/api/auditoria/verificar` | requerida | Comprueba que la cadena de hash de la auditoría no fue alterada |
| GET | `/api/auth/estado` | pública | Permite al frontend saber si debe mostrar la pantalla de acceso |
| POST | `/api/auth/login` | pública | Inicia sesión con el PIN y devuelve un token |
| POST | `/api/auth/logout` | requerida | Cierra la sesión actual |
| POST | `/api/auth/recuperar` | pública | Restablece el PIN con el código de recuperación |
| POST | `/api/auth/reiniciar-pin/{tid}` | requerida | El comandante reinicia el PIN de otro tripulante |
| GET | `/api/auth/yo` | requerida | Quién es el usuario de la sesión actual y cuál es su rol |

## lecturas

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/alertas/colectivas` | requerida | Cruce de CO2 de cabina con el estado de la tripulación |
| GET | `/api/estado/{tid}` | requerida | Estado clínico vigente de un tripulante: niveles, NEWS2, reglas y acciones sugeridas |
| GET | `/api/historial/{tid}` | requerida | Serie temporal de un indicador (para gráficas). El ánimo diario es privado y no sale por aquí |
| POST | `/api/lecturas` | requerida | Cualquier tripulante autenticado puede registrar signos de un compañero (p. ej. si este queda incapacitado) |
| GET | `/api/racha/{tid}` | requerida | Racha de días con los 5 signos vitales registrados y logros ligeros, sin presión |
| GET | `/api/recordatorios` | requerida | Quién tiene la medición vencida, según su nivel actual y su frecuencia de recordatorios elegida |
| GET | `/api/recordatorios/{tid}` | requerida | Indica si la medición de un tripulante está vencida o al día |

## bienestar

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| POST | `/api/animo` | requerida | Ánimo diario de 1 a 5. Exclusivo de su dueño y nunca se transmite |
| GET | `/api/animo/{tid}` | requerida | Serie del ánimo diario del propio tripulante (privado) |
| POST | `/api/crisis/aviso-medico` | requerida | Notifica al comandante con consentimiento explícito. Nunca entra a la cola hacia Tierra |
| GET | `/api/crisis/avisos` | requerida | Vista exclusiva del comandante: solo muestra avisos con consentimiento vigente |
| POST | `/api/crisis/avisos/{aviso_id}/atender` | requerida | El comandante marca un aviso de salud mental como atendido |
| POST | `/api/crisis/avisos/{aviso_id}/revocar` | requerida | El propio tripulante revoca su consentimiento: el aviso deja de ser visible para el comandante |
| GET | `/api/crisis/avisos/{tid}` | requerida | Avisos que el propio tripulante compartió con el comandante y su estado (pendiente, atendido o revocado) |
| GET | `/api/crisis/protocolo` | requerida | Protocolo de crisis psicológica / riesgo de autolesión, integrando tono y calidad de oxígeno en cabina |
| POST | `/api/diario` | requerida | Guarda en local. Por diseño no escribe en la cola de salida |
| GET | `/api/diario/{tid}` | requerida | Notas del diario del propio tripulante (privado) |
| GET | `/api/preferencias/{tid}` | requerida | Cómo quiere cada tripulante que le hable el asistente. Solo cambia la forma, nunca el nivel de alerta |
| PUT | `/api/preferencias/{tid}` | requerida | Guarda el tono, el detalle y los recordatorios elegidos por el tripulante |
| POST | `/api/tamizajes` | requerida | Registra un PHQ-2 y, si procede, devuelve el protocolo de apoyo (privado) |

## enlace

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/cola` | requerida | Cola de salida: resumen por estado y eventos recientes |
| GET | `/api/cola/verificar` | requerida | Comprueba que la cadena de hash de la cola no fue alterada |
| GET | `/api/enlace` | requerida | Estado actual del enlace con Tierra (activo o eclipse, y entorno) |
| POST | `/api/enlace` | requerida | Cambia el estado o el entorno del enlace y despacha lo retenido si hay enlace |
| GET | `/api/enlace/latencia` | requerida | Perfil de retardo en uso, factor de aceleración y eventos en tránsito |
| GET | `/api/tierra/mensajes` | requerida | Vista del centro de control: solo lo que ya llegó por la hora estimada, lo urgente primero |

## informe

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/informe` | requerida | Resumen de toda la tripulación para Tierra, con huella de integridad. Sin datos personales privados |
| GET | `/api/informe/{tid}` | requerida | Informe de un tripulante. `formato=csv` devuelve solo las lecturas, listas para una hoja de cálculo |

## sensores

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| POST | `/api/sensores/flujo` | requerida | Una muestra de un flujo continuo (p. ej. una banda): se agrupa por ventanas, salvo los valores extremos |
| POST | `/api/sensores/flujo/lote` | requerida | Varias muestras de un flujo continuo en una sola petición (hasta 500); todo o nada si alguna es inválida |
| POST | `/api/sensores/flujo/vaciar` | requerida | Cierra ya las ventanas abiertas y registra su resumen (útil al desconectar un dispositivo) |
| POST | `/api/sensores/lectura` | requerida | Entrada de un dispositivo: misma clasificación y misma cola que la captura manual, con origen 'sensor' |
| POST | `/api/sensores/lote` | requerida | Varias lecturas de un dispositivo. Todo o nada: si una es inválida no se guarda ninguna |

## demo

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| GET | `/api/demo/comparativa` | requerida | Mismo evento (hipoxia severa) visto con y sin ORBIT. No escribe datos; es una ilustración con supuestos |
| GET | `/api/demo/escenarios` | requerida | Lista de escenarios de demostración disponibles |
| POST | `/api/demo/escenarios/{nombre}` | requerida | Ejecuta un escenario guionizado. Escribe datos de demostración; desactivar con ORBIT_DEMO_API=0 |
| POST | `/api/demo/sensor/{tid}` | requerida | Un dispositivo portátil simulado envía `ticks` rondas de constantes vitales (origen 'sensor'). Escribe datos de demo |
| POST | `/api/demo/simulacion/detener` | requerida | Detiene la misión simulada, cierra las ventanas abiertas y devuelve el enlace a la normalidad |
| GET | `/api/demo/simulacion/estado` | requerida | Progreso de la misión simulada: minuto, línea de tiempo narrada y hitos (primer rojo, alerta colectiva, retenidos) |
| POST | `/api/demo/simulacion/iniciar` | requerida | Pone en marcha una misión simulada en vivo: las bandas envían solas, el enlace se corta y vuelve. Escribe datos de demo |

## asistente

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| POST | `/api/asistente/chat/{tid}` | requerida | Conversa por texto con tu asistente de apoyo. Privado: solo el propio astronauta. No requiere la voz |
| GET | `/api/estado/{tid}/explicacion` | requerida | Explica un estado ya calculado con reglas locales o un modelo local opcional |
| GET | `/api/perfil-ia/{tid}` | requerida | Intereses que el propio astronauta le cuenta a su asistente (privado: solo su dueño) |
| PUT | `/api/perfil-ia/{tid}` | requerida | Guarda sus intereses y motivadores (máx. 160 caracteres). Solo se usan con un modelo local |

## voz

| Método | Ruta | Sesión | Qué hace |
|---|---|---|---|
| POST | `/api/voz/chat/{tid}` | requerida | Transcribe audio localmente, responde con el LLM local y devuelve audio opcional |

Total: 63 operaciones, 13 públicas.
