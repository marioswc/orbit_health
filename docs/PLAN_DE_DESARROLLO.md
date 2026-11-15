# ORBIT Health — Plan de desarrollo

Sistema de apoyo a la decisión clínica para tripulaciones en misiones de espacio profundo con comunicación degradada. Funciona 100 % local, sin internet, con reglas clínicas deterministas y auditables.

> **Nota:** este es el plan inicial del día. El estado vigente está en [PENDIENTES.md](PENDIENTES.md) y las rutas reales en [API_REFERENCIA.md](API_REFERENCIA.md).

> **Alcance:** prototipo funcional construido desde cero en este repositorio. Es una herramienta de apoyo; no sustituye criterio médico. Todo umbral marcado como *Supuesto* requiere validación por un profesional de la salud antes de uso real.

---

## 1. Objetivo y principios

| Principio | Qué significa en el diseño |
|---|---|
| Autonomía | Todo corre en local; ninguna función depende de red |
| Determinismo | Reglas explícitas y trazables; sin modelos de caja negra en la decisión primaria |
| Línea base personal | Cada tripulante se compara contra su propio historial reciente además de contra rangos fijos |
| Privacidad | El diario personal nunca entra a la cola de salida |
| Resiliencia | Si el enlace cae, los eventos se retienen y salen por prioridad al volver |

## 2. Problema que resolvemos

- Con latencia de minutos y enlaces intermitentes, el control en Tierra no puede decidir en tiempo real.
- Supuesto: retardo unidireccional hasta ~20 min en Marte y ~1.3 s en la Luna (verificar cifras con fuente oficial antes de citarlas).
- La tripulación necesita triaje inmediato a bordo, registro confiable y envío ordenado cuando haya enlace.

## 3. Alcance

| Entra | No entra (declarado) |
|---|---|
| Captura manual de signos vitales | Telemetría de sensores reales |
| Puntuación NEWS2 y nivel verde/amarillo/rojo | Diagnóstico clínico definitivo |
| Línea base móvil de 14 días (alerta a >2 DE) | Modelos de aprendizaje en línea |
| Calidad de aire (CO₂) y dosis acumulada | Actividad extravehicular, descompresión, cargas dinámicas |
| Tamizaje PHQ-2 confidencial | Comunicación con el comandante sin consentimiento |
| Diario privado local | Sincronización a la nube |
| Cola store-and-forward con prioridad y hash encadenado | Transmisión real de radio |
| Consola de enlace con Modo Eclipse (simulado) | |

## 4. Arquitectura

```
React + TS (build estático) ──HTTP local──▶ api (routers FastAPI)
                                              │
                                          servicios (casos de uso)
                                           │            │
                                    repositorios      dominio
                                    (SQL, SQLite)   (reglas, hash,
                                                     umbrales.json)
```

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Frontend | React, TypeScript, build estático | Captura, visualización, consola de enlace |
| Backend | Python, FastAPI | API REST y motor clínico |
| Datos | SQLite con `foreign_keys=ON` y WAL | Persistencia local |

Estructura del repo: ver README. Backend por capas (`api`, `servicios`, `repositorios`, `dominio`, `fuentes`); umbrales clínicos en `backend/app/datos/umbrales.json`.

## 5. Modelo de datos

| Tabla | Propósito | Campos clave |
|---|---|---|
| `tripulantes` | Perfil | id, nombre, rol, fecha_nacimiento |
| `lecturas` | Mediciones | tripulante_id, indicador, valor, unidad, nivel, puntos_news2, origen, ts |
| `cola_salida` | Eventos hacia Tierra | prioridad (1–3), payload, hash_prev, hash, estado (`retenido`/`en_transito`/`recibido`), ts |
| `diario_privado` | Notas personales | tripulante_id, contenido, ts. **Sin relación con `cola_salida`** |
| `tamizajes` | PHQ-2 y pregunta de riesgo | tripulante_id, item1, item2, total, riesgo_autolesion, nivel_protocolo, ts. Acceso solo del propio tripulante |
| `capsulas` | Guías de autorregulación | categoría, título, contenido |
| `animo_diario` | Ánimo 1 a 5, privado | tripulante_id, valor, ts |
| `preferencias` | Tono, detalle y recordatorios que elige cada tripulante | tripulante_id, tono, detalle, recordatorios |
| `avisos_salud_mental` | Aviso que el tripulante decide enviar al médico o comandante | tipo, nivel_protocolo, mensaje_opcional, consentimiento, estado. Sin relación con `cola_salida` |
| `credenciales`, `sesiones` | Acceso por PIN, sesiones revocables | PIN y código de recuperación solo como hash |
| `auditoria` | Registro encadenado con hash | actor, acción, objetivo, ts |
| `estado_enlace` | Enlace con Tierra persistente | activo, entorno |

Reglas de integridad:
- Índice por (tripulante, ts) en `lecturas` y por (estado, prioridad, creado) en la cola.
- **Hash encadenado verificable:** `hash = SHA-256(hash_prev | campos del evento | ts_guardado)`. El `ts` se persiste para poder recomputarlo; se incluye un verificador de cadena.

El explicador local opcional (`GET /api/estado/{tid}/explicacion`) recibe únicamente el estado ya calculado. Su salida es informativa: no puede modificar niveles, prioridades, acciones ni la cola. Si no hay un modelo local configurado, devuelve una explicación determinista.

## 6. Reglas clínicas

### 6.1 NEWS2 (fuente: Royal College of Physicians, 2017 — verificar tablas contra la publicación)

Variables: frecuencia respiratoria, SpO₂ (escala 1), presión sistólica, frecuencia cardíaca, conciencia (AVPU), temperatura.

| Resultado | Condición | Nivel |
|---|---|---|
| 0–4 sin parámetro en 3 | Riesgo bajo | Verde |
| 5–6, o un parámetro en 3 | Riesgo medio / respuesta urgente | Amarillo |
| ≥ 7 | Riesgo alto | Rojo |

**Decisión tomada por el equipo: opción B** (ver `docs/DECISIONES_EQUIPO.md`; sigue pendiente de validación médica). El esquema RCP trata un parámetro aislado en 3 como urgente, no como máxima alerta. Opciones consideradas:

| Opción | Pro | Contra |
|---|---|---|
| A. Seguir RCP (parámetro en 3 = amarillo) | Fiel a la fuente, defendible | Una hipoxia severa aislada no sale roja |
| B. Parámetro en 3 = rojo (criterio conservador propio) | Prioriza seguridad en aislamiento | Se aparta del estándar; declararlo como adaptación |

Se eligió B, documentada como adaptación propia y sujeta a validación médica.

### 6.2 Línea base personal
- Media y desviación estándar muestral de los últimos 14 días por indicador.
- Aviso preventivo si el valor se aleja más de 2 DE. Requiere un mínimo de muestras (*Supuesto:* N ≥ 5; ajustar al calibrar).

### 6.3 Ambiente y dosis
| Parámetro | Verde | Amarillo | Rojo |
|---|---|---|---|
| CO₂ (mmHg) | ≤ 3.0 | 3.1–4.0 | > 4.0 |
| Dosis acumulada (% del límite de misión) | < 70 | 70–89 | ≥ 90 |

*Supuesto:* todos los umbrales de esta tabla son de diseño y no tienen fuente validada. Verificar con literatura de calidad de aire en hábitats cerrados.

### 6.4 PHQ-2
Puntaje 0–6; ≥ 3 es positivo en tamizaje. Resultado visible solo para el tripulante, con cápsulas de apoyo. No genera eventos en la cola ni avisos al resto de la tripulación. *Es tamizaje, no diagnóstico.*

### 6.5 Otros umbrales
Glucemia capilar y presión diastólica baja quedan como **observación**, no como alerta mayor. *Supuesto:* rangos pendientes de validación médica.

## 7. Cola de transmisión (Modo Eclipse)

| Estado del enlace | Comportamiento |
|---|---|
| Activo | Drena por prioridad (1 → 2 → 3) y por antigüedad dentro de cada una |
| Eclipse | Retiene todo; nada sale |
| Latencia | Simulada con factor de aceleración configurable (variable de entorno) |

Prioridad: rojo = 1, amarillo = 2, verde = 3.

## 8. Frontend

| Componente | Función |
|---|---|
| Figura humana (SVG) | Estado por zona corporal; transiciones CSS, sin filtros pesados |
| Panel de medición | Captura manual con validación de rango fisiológico |
| Diario del tripulante | Texto libre con etiqueta "Almacenamiento local, sin telemetría externa" |
| Consola de enlace | Luna/Marte, normal/eclipse, cola agrupada por prioridad |
| Tamizaje PHQ-2 | Cuestionario privado y cápsulas |

## 9. Plan de trabajo de hoy

Supuesto: bloques ordenados por dependencia; ajustar tiempos al equipo.

| # | Bloque | Entregable | Criterio de salida |
|---|---|---|---|
| 1 | Base del repo | Estructura, este plan, `.env.example` | Primer commit solo con este documento |
| 2 | Datos | Esquema SQLite y migración inicial | Tablas creadas con claves foráneas activas |
| 3 | Motor clínico | NEWS2, ambiente, línea base | Pruebas unitarias en verde |
| 4 | Cola | Encolado, hash verificable, despacho | Pruebas de prioridad y de cadena |
| 5 | API | Endpoints de lecturas, diario, tamizaje, enlace | Pruebas de integración en verde |
| 6 | Frontend | Panel, figura, diario, consola | Flujo completo en build de producción |
| 7 | Verificación | Prueba offline E2E | Flujo completo con red desactivada |
| 8 | Demo | Guion y ensayo | Recorrido de 3 min sin fallos |

## 10. Pruebas obligatorias

| Prueba | Verifica |
|---|---|
| NEWS2 por caso | Puntos y nivel contra tabla de referencia, incluidos bordes |
| Alerta severa | Parámetro en 3 produce el nivel decidido en 6.1 y prioridad 1 |
| Diario aislado | Escribir en el diario no crea filas en `cola_salida` |
| Prioridad en eclipse | Tras reconectar, el primer despacho es prioridad 1 |
| Cadena de hash | Modificar un evento rompe la verificación |
| PHQ-2 privado | El resultado no aparece en la cola ni en endpoints de otros tripulantes |
| Offline E2E | Sin red, sin errores por recursos externos (sin CDN ni fuentes remotas) |

## 11. Seguridad y deuda conocida

- Configuración (rutas, factor de aceleración) por variables de entorno; sin secretos en el código.
- Datos de salud: en este prototipo, la base local no está cifrada. Para uso real, cifrar en reposo y controlar acceso por tripulante.
- Sin autenticación en el prototipo; el acceso al diario y al PHQ-2 depende de ello. Declararlo en la demo.

## 12. Datos de calibración

| Aspecto | Detalle |
|---|---|
| Conjunto | BIDMC PPG and Respiration Dataset v1.0.0 (PhysioNet), DOI 10.13026/C2208R, licencia ODC-By 1.0 |
| Variables usadas | Frecuencia cardíaca, frecuencia respiratoria y SpO₂ (1 Hz) |
| Procesamiento | Mediana por ventana de 20 s; lecturas con `origen='calibracion'`, fuera de la cola de salida |
| Operación | Descarga con red una sola vez (`scripts/descargar_physionet.sh`, verifica SHA-256); carga sin red (`scripts/cargar_calibracion.sh`) |
| Limitación | Los registros son de **pacientes críticos hospitalizados**, no de personas sanas ni de tripulantes |

Redacción permitida: "series públicas de PhysioNet usadas para dar variabilidad realista a la demo y a las pruebas".
No decir: "validado clínicamente", "línea base de astronautas" ni "calibrado para población sana".
Para uso real habría que reemplazar la calibración por mediciones propias de cada tripulante.

## 13. Guion de demo (3 min)

| Tiempo | Contenido |
|---|---|
| 0:00–0:40 | Problema: enlaces lentos o caídos y necesidad de decidir a bordo |
| 0:40–1:30 | Enfoque: reglas deterministas, línea base personal, datos públicos de calibración |
| 1:30–2:20 | Demo sin red: lectura crítica, eclipse, eventos retenidos, reconexión con salida por prioridad |
| 2:20–3:00 | Privacidad: diario y PHQ-2 aislados; límites y validación médica pendiente |

## 14. Pendientes para humano

- Validación médica de todos los umbrales marcados como *Supuesto*.
- Decisión de la opción A o B en 6.1.
- Confirmar fuentes de cifras antes de usarlas en la presentación.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
