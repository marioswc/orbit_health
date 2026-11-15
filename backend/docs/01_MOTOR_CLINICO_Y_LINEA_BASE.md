# 01 — Motor Clínico, Reglas Combinadas y Línea Base Personal

Este módulo es el corazón médico de **ORBIT Health**. Su trabajo es recibir cualquier medición de un tripulante o del ambiente de la cabina y decidir de forma inmediata, sin internet y sin "cajas negras", si todo está normal (**verde**), si requiere atención preventiva (**amarillo**) o si es una emergencia (**rojo**).

---

## 1. Umbrales médicos separados del código (`umbrales.json`)

### Qué problema había
Al principio (`commit fdabb9f`), los rangos de qué era normal o peligroso (frecuencia cardíaca, oxígeno, presión, fiebre) estaban escritos directamente dentro del código Python. Si un médico quería revisar o ajustar un valor, tenía que leer programación.

### Cómo se solucionó (`commits 5ad906b`, `ec36acc`, `543ad61`, `17708a2`)
- Se sacaron todas las tablas y límites al archivo `backend/app/datos/umbrales.json`.
- El módulo `backend/app/dominio/umbrales.py` lee ese archivo al arrancar y comprueba que no le falte ningún dato ni tenga errores de formato.
- Se creó la ruta pública `GET /api/umbrales` para que la interfaz muestre qué versión de reglas se está usando y recuerde siempre que los valores marcados como *supuestos* están pendientes de validación médica.
- También se definió ahí cada cuántos minutos debe volver a medirse un tripulante según su gravedad (`captura_recomendada_min`): **60 minutos** en verde, **15 minutos** en amarillo y **5 minutos** en rojo.
- **Perfil poblacional y semántica del semáforo (`commit 17708a2`):**
  - `GET /api/umbrales` también expone el **perfil poblacional** (`adultos_tripulantes_general`, de tipo `experimental`), los parámetros del método estadístico de la línea base y el significado exacto de cada color del **semáforo**.
  - Cada lectura registrada (`POST /api/lecturas`) devuelve `estado_semaforo` (`sin_alerta`, `observacion`, `seguimiento` o `urgente`) y `linea_base_estado` (`insuficiente` cuando aún no se reúnen las 5 muestras mínimas, `normal` o `aviso`), dejando claro que **verde significa "sin alerta activada con los datos disponibles", no un diagnóstico médico de normalidad**.

---

## 2. Evaluación NEWS2 y otros indicadores individuales

### Cómo funciona (`backend/app/dominio/reglas.py`)
1. **Escala NEWS2 (6 signos vitales principales):** evalúa frecuencia respiratoria, saturación de oxígeno (`spo2`), presión sistólica, frecuencia cardíaca, nivel de alerta (`avpu`) y temperatura.
   - Cada signo suma de 0 a 3 puntos según qué tan lejos esté de lo normal.
   - **Decisión de seguridad a bordo (`MODO_PARAMETRO_EXTREMO = conservador`):** en un hospital en Tierra, tener un solo signo en 3 puntos se marca como alerta media (amarillo). En el espacio, el equipo decidió que **un solo signo extremo (3 puntos, como una caída grave de oxígeno) dispare directamente alerta roja**, priorizando la seguridad en aislamiento.
2. **Ambiente de cabina (`evaluar_ambiente`):** vigila el dióxido de carbono (`co2_mmhg`), el porcentaje de oxígeno en el aire (`o2_cabina`, que alerta tanto si falta oxígeno como si hay exceso con riesgo de incendio) y la radiación acumulada (`dosis_pct`).
3. **Glucosa y presión diastólica:** evalúan rangos de alerta o dejan una nota de *observación* cuando están ligeramente bajas sin llegar a ser una emergencia (`estado_semaforo = "observacion"`).
4. **Horas de sueño (`sueno_horas`) y ejercicio (`ejercicio_min`) (`commits ea13926`, `27c754e`):** dormir poco genera un aviso preventivo (**amarillo**, nunca rojo por sí solo), y los minutos de ejercicio permiten dar seguimiento al acondicionamiento físico en el espacio.
5. **Calidad de sueño por actigrafía (`sueno_eficiencia_pct` y `sueno_despertares_min`, `commit e143eb0`) y Variabilidad Cardíaca (`variabilidad_cardiaca`, `commit f8a3cec`):**
   - Inspirados en los estudios de actigrafía de la NASA (ARCHeR) y de adaptación autonómica cardiovascular, estos tres indicadores **no tienen un umbral fijo universal** (una lectura aislada es `verde`), sino que se evalúan comparando al tripulante contra su propia línea base personal.

---

## 3. Reglas Combinadas y Alertas Colectivas de Cabina

### Qué problema había
Evaluar cada signo por separado no siempre basta: dos signos que por sí solos están en "amarillo" pueden significar un riesgo alto si ocurren al mismo tiempo. Además, si el CO₂ o la caída de O₂ de la cabina afecta a varios tripulantes a la vez, no es una coincidencia individual, sino un problema ambiental de toda la nave.

### Cómo se solucionó (`commits b069188`, `0a647e6`, `49ee74c`, `ce363f8`)
En `backend/app/dominio/combinadas.py` y `backend/app/servicios/alertas.py` se implementaron dos niveles de cruce:
1. **Reglas combinadas individuales:** cruzan los signos recientes de un mismo tripulante (por ejemplo, `deterioro_respiratorio` por hipoxia con taquipnea, `posible_proceso_infeccioso` por fiebre con taquicardia, o `posible_intolerancia_ortostatica` por taquicardia con caída de presión). Si se cumple una combinación de riesgo, el nivel del tripulante sube automáticamente y el sistema explica qué regla combinada se activó.
2. **Alertas colectivas de cabina (`GET /api/alertas/colectivas`):**
   - Cruzan tanto el nivel de **CO₂** como el de **oxígeno en cabina (`o2_cabina`)** con el estado de salud de toda la tripulación.
   - **Solución a una falsa alarma importante:** antes, si se registraba una lectura ambiental de CO₂ alta, esa misma lectura subía el estado general del tripulante y hacía creer al sistema que ya había "varios tripulantes enfermos". Se corrigió separando el **nivel fisiológico** (solo signos del cuerpo) del nivel ambiental, de modo que la alerta colectiva solo se dispara cuando el aire está mal **y además** los cuerpos de los tripulantes realmente están mostrando signos alterados.

---

## 4. Línea Base Personal (14 días) y Corrección de Falsas Alarmas

Cada persona tiene su propio ritmo normal (por ejemplo, un astronauta deportista puede tener pulsaciones bajas de forma natural). Por eso, además de usar tablas fijas, ORBIT Health compara cada lectura con el promedio y la variación de los **últimos 14 días de ese mismo tripulante** (`GET /api/estado/{tid}`).

Durante el desarrollo surgieron **tres necesidades reales** con esta fórmula estadística y así se solucionaron:

### Problema A: "Dormir más, hacer más ejercicio o tener mayor variabilidad cardíaca daba alerta" (`commits 27c754e`, `e143eb0`, `f8a3cec`)
- **Qué pasaba:** la fórmula original avisaba siempre que un valor se alejaba mucho de la costumbre, tanto hacia arriba como hacia abajo (`direccion = "dos_lados"`). Si un tripulante dormía más horas, tenía mayor eficiencia de sueño, hacía más ejercicio, tenía mejor ánimo o subía su variabilidad cardíaca (mejor recuperación vagal), el sistema le lanzaba un aviso de anomalía.
- **Cómo se solucionó (`solo_baja=True`):** en `sueno_horas`, `sueno_eficiencia_pct`, `ejercicio_min`, `variabilidad_cardiaca` y `animo`, el sistema marca `direccion = "baja"` y **solo avisa cuando el valor cae por debajo de lo habitual**, nunca cuando mejora.

### Problema B: "Despertarse menos tiempo en la noche daba alerta" (`commit e143eb0`)
- **Qué pasaba:** al incorporar `sueno_despertares_min` (minutos que el tripulante pasó despierto durante la noche), ocurriría lo contrario: tener *menos* minutos despierto que de costumbre es buena señal; lo que preocupa es pasar *más* tiempo despierto que lo habitual.
- **Cómo se solucionó (`solo_alta=True`):** se añadió el parámetro `solo_alta` en `desviacion_linea_base` (`direccion = "alta"`), de modo que `sueno_despertares_min` **solo avisa cuando supera el rango habitual del tripulante**.

### Problema C: "Un tripulante demasiado estable disparaba falsas alarmas" (`commit 7ff5998`)
- **Qué pasaba:** si un tripulante tenía signos casi idénticos durante varios días (por ejemplo, siempre 62 latidos por minuto), su variación matemática (desviación estándar) era prácticamente cero. En el momento en que subía a 66 latidos —algo completamente normal y sano—, matemáticamente parecía un cambio gigante y el sistema lo ponía en amarillo e incluso disparaba alertas colectivas falsas.
- **Cómo se solucionó:** se creó un **piso mínimo de variación** por indicador en `umbrales.json` (`piso_desviacion`: por ejemplo, mínimo 4 lpm en frecuencia cardíaca, 1.5 % en SpO₂, 3 % en eficiencia de sueño, 10 min en despertares o 8 ms en variabilidad cardíaca). Así, aunque el historial de una persona sea plano como una regla, el sistema nunca exagera variaciones pequeñas y normales del cuerpo humano.

---

## 5. Acciones Sugeridas sin Recetar Tratamientos

### Qué problema había
Decirle a un tripulante "estás en amarillo o rojo" sin indicarle qué paso sigue genera incertidumbre, pero el sistema tampoco puede recetar fármacos ni sustituir a un médico.

### Cómo se solucionó (`commit dc6a694`)
En `backend/app/dominio/acciones.py` se creó un generador de **pasos procedimentales** que acompaña a cada lectura (`POST /api/lecturas`) y a cada consulta de estado (`GET /api/estado/{tid}`):
- Indica pasos prácticos y seguros: repetir la medición para descartar un mal contacto, guardar reposo, avisar al médico o compañero de guardia, verificar el suministro de aire si el problema es respiratorio y completar los signos vitales que falten para cerrar el cálculo de NEWS2.
- Una prueba automática (`backend/tests/test_acciones.py`) vigila que ningún texto sugiera jamás medicamentos ni tratamientos clínicos.
