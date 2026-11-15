# 01 — Motor Clínico, Reglas Combinadas y Línea Base Personal

Este módulo es el corazón médico de **ORBIT Health**. Su trabajo es recibir cualquier medición de un tripulante o del ambiente de la cabina y decidir de forma inmediata, sin internet y sin "cajas negras", si todo está normal (**verde**), si requiere atención preventiva (**amarillo**) o si es una emergencia (**rojo**).

---

## 1. Umbrales médicos separados del código (`umbrales.json`)

### Qué problema había
Al principio (`commit fdabb9f`), los rangos de qué era normal o peligroso (frecuencia cardíaca, oxígeno, presión, fiebre) estaban escritos directamente dentro del código Python. Si un médico quería revisar o ajustar un valor, tenía que leer programación.

### Cómo se solucionó (`commits 5ad906b`, `ec36acc`, `543ad61`)
- Se sacaron todas las tablas y límites al archivo `backend/app/datos/umbrales.json`.
- El módulo `backend/app/dominio/umbrales.py` lee ese archivo al arrancar y comprueba que no le falte ningún dato ni tenga errores de formato.
- Se creó la ruta pública `GET /api/umbrales` para que la interfaz muestre qué versión de reglas se está usando y recuerde siempre que los valores marcados como *supuestos* están pendientes de validación médica.
- También se definió ahí cada cuántos minutos debe volver a medirse un tripulante según su gravedad (`captura_recomendada_min`): **60 minutos** en verde, **15 minutos** en amarillo y **5 minutos** en rojo.

El endpoint `GET /api/umbrales` también expone el perfil poblacional, el estado de validación y la semántica del
semáforo. El perfil actual es experimental para adultos astronautas y no pretende reemplazar ajustes individualizados.
Un resultado verde significa únicamente que no se activó una alerta con los datos disponibles; no es un diagnóstico de
normalidad. La línea base informa explícitamente cuando todavía hay muestras insuficientes, cuando el valor está dentro
del límite configurado y cuando se activa un aviso.

---

## 2. Evaluación NEWS2 y otros indicadores individuales

### Cómo funciona (`backend/app/dominio/reglas.py`)
1. **Escala NEWS2 (6 signos vitales principales):** evalúa frecuencia respiratoria, saturación de oxígeno (`spo2`), presión sistólica, frecuencia cardíaca, nivel de alerta (`avpu`) y temperatura.
   - Cada signo suma de 0 a 3 puntos según qué tan lejos esté de lo normal.
   - **Decisión de seguridad a bordo (`MODO_PARAMETRO_EXTREMO = conservador`):** en un hospital en Tierra, tener un solo signo en 3 puntos se marca como alerta media (amarillo). En el espacio, el equipo decidió que **un solo signo extremo (3 puntos, como una caída grave de oxígeno) dispare directamente alerta roja**, priorizando la seguridad en aislamiento.
2. **Ambiente de cabina (`evaluar_ambiente`):** vigila el dióxido de carbono (`co2_mmhg`), el porcentaje de oxígeno en el aire (`o2_cabina`, que alerta tanto si falta oxígeno como si hay exceso con riesgo de incendio) y la radiación acumulada (`dosis_pct`).
3. **Glucosa y presión diastólica:** evalúan rangos de alerta o dejan una nota de *observación* cuando están ligeramente bajas sin llegar a ser una emergencia.
4. **Horas de sueño (`sueno_horas`) y ejercicio (`ejercicio_min`) (`commits ea13926`, `27c754e`):** dormir poco genera un aviso preventivo (**amarillo**, nunca rojo por sí solo), y los minutos de ejercicio permiten dar seguimiento al acondicionamiento físico en el espacio.

---

## 3. Reglas Combinadas y Alerta Colectiva de CO₂

### Qué problema había
Evaluar cada signo por separado no siempre basta: dos signos que por sí solos están en "amarillo" pueden significar un riesgo alto si ocurren al mismo tiempo. Además, si el CO₂ de la cabina sube y varios tripulantes empiezan a presentar síntomas, no es una coincidencia individual, sino un problema ambiental de toda la nave.

### Cómo se solucionó (`commits b069188`, `0a647e6`, `49ee74c`)
En `backend/app/dominio/combinadas.py` y `backend/app/servicios/alertas.py` se implementaron dos niveles de cruce:
1. **Reglas combinadas individuales:** cruzan los signos recientes de un mismo tripulante (por ejemplo, hipoxia combinada con respiración acelerada, o fiebre con taquicardia). Si se cumple una combinación de riesgo, el nivel del tripulante sube automáticamente y el sistema explica qué regla combinada se activó.
2. **Alerta colectiva de cabina (`GET /api/alertas/colectivas`):**
   - Cruza el nivel de CO₂ de la nave con el estado de salud de toda la tripulación.
   - **Solución a una falsa alarma importante:** antes, si se registraba una lectura ambiental de CO₂ alta, esa misma lectura subía el estado general del tripulante y hacía creer al sistema que ya había "varios tripulantes enfermos". Se corrigió separando el **nivel fisiológico** (solo signos del cuerpo) del nivel ambiental, de modo que la alerta colectiva solo se dispara cuando el aire está mal **y además** los cuerpos de los tripulantes realmente están mostrando signos alterados.

---

## 4. Línea Base Personal (14 días) y Corrección de Falsas Alarmas

Cada persona tiene su propio ritmo normal (por ejemplo, un astronauta deportista puede tener pulsaciones bajas de forma natural). Por eso, además de usar tablas fijas, ORBIT Health compara cada lectura con el promedio y la variación de los **últimos 14 días de ese mismo tripulante** (`GET /api/estado/{tid}`).

Durante el desarrollo surgieron **dos problemas reales** con esta fórmula estadística y así se solucionaron:

### Problema A: "Dormir más o hacer más ejercicio daba alerta" (`commit 27c754e`)
- **Qué pasaba:** la fórmula avisaba siempre que un valor se alejaba mucho de la costumbre, tanto hacia arriba como hacia abajo. Si un tripulante dormía más horas que de costumbre, hacía más ejercicio o tenía mejor ánimo, el sistema le lanzaba un aviso de anomalía.
- **Cómo se solucionó:** se agregó el criterio unilateral (`solo_baja=True` en `desviacion_linea_base`). En sueño, ejercicio y ánimo, el sistema **solo avisa cuando el valor cae por debajo de lo habitual**, nunca cuando mejora.

### Problema B: "Un tripulante demasiado estable disparaba falsas alarmas" (`commit 7ff5998`)
- **Qué pasaba:** si un tripulante tenía signos casi idénticos durante varios días (por ejemplo, siempre 62 latidos por minuto), su variación matemática (desviación estándar) era prácticamente cero. En el momento en que subía a 66 latidos —algo completamente normal y sano—, matemáticamente parecía un cambio gigante y el sistema lo ponía en amarillo e incluso disparaba alertas colectivas falsas.
- **Cómo se solucionó:** se creó un **piso mínimo de variación** por indicador en `umbrales.json` (`piso_desviacion`: por ejemplo, mínimo 4 lpm en frecuencia cardíaca o 1.5 % en SpO₂). Así, aunque el historial de una persona sea plano como una regla, el sistema nunca exagera variaciones pequeñas y normales del cuerpo humano.

---

## 5. Acciones Sugeridas sin Recetar Tratamientos

### Qué problema había
Decirle a un tripulante "estás en amarillo o rojo" sin indicarle qué paso sigue genera incertidumbre, pero el sistema tampoco puede recetar fármacos ni sustituir a un médico.

### Cómo se solucionó (`commit dc6a694`)
En `backend/app/dominio/acciones.py` se creó un generador de **pasos procedimentales** que acompaña a cada lectura (`POST /api/lecturas`) y a cada consulta de estado (`GET /api/estado/{tid}`):
- Indica pasos prácticos y seguros: repetir la medición para descartar un mal contacto, guardar reposo, avisar al médico o compañero de guardia, verificar el suministro de aire si el problema es respiratorio y completar los signos vitales que falten para cerrar el cálculo de NEWS2.
- Una prueba automática (`backend/tests/test_acciones.py`) vigila que ningún texto sugiera jamás medicamentos ni tratamientos clínicos.
