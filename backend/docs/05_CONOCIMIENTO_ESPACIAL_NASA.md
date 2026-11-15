# 05 — Conocimiento Espacial: Riesgos NASA, Explicaciones y Entornos

Un sistema para misiones espaciales no solo debe medir números, sino también **contextualizar qué significan esos números fuera de la Tierra**, basándose únicamente en fuentes oficiales verificables y sin inventar afirmaciones científicas.

---

## 1. Marco de Peligros y Riesgos de la NASA (`/api/peligros`)

### Qué problema había
El reto de la NASA pide relacionar la salud de la tripulación con los peligros reales del vuelo espacial definidos por el *Human Research Program (HRP)*, pero existía el riesgo de exagerar diciendo que el software "cubría todos los riesgos espaciales".

### Cómo se solucionó (`commits dfa2fa2`, `27c754e`, `e143eb0`, `f8a3cec`)
En `backend/app/datos/peligros.json` y `backend/app/dominio/peligros.py` (`GET /api/peligros`):
- Se catalogaron los **5 grandes peligros de los vuelos espaciales** (radiación, aislamiento y confinamiento, distancia de la Tierra, campos de gravedad y entornos hostiles/cerrados) y los **17 riesgos oficiales del HRP**, cada uno con su enlace oficial a `nasa.gov`.
- **Honestidad en la cobertura:** cada riesgo declara qué tanto lo cubre realmente ORBIT Health hoy:
  - **1 riesgo cubierto** (atención médica autónoma ante distancia de la Tierra).
  - **7 riesgos cubiertos parcialmente** (como CO₂, sueño incluyendo eficiencia y despertares por actigrafía, conducta/ánimo, cardiovascular incluyendo variabilidad cardíaca, y ejercicio).
  - **9 riesgos no cubiertos** (como síndrome neuro-ocular, polvo lunar o EVA, que requieren equipos médicos especializados).
- Cada alerta médica y el estado de cada tripulante (`GET /api/estado/{tid}`) incluyen automáticamente el campo `peligros_relacionados` para mostrar con qué peligro espacial se conecta esa anomalía.
- Pruebas automáticas (`backend/tests/test_peligros.py` y `backend/tests/test_documentacion.py`) verifican que todos los enlaces sean oficiales y que ningún documento del repositorio infle estas cifras.

---

## 2. Explicaciones Educativas y Citas Textuales de la NASA (`/api/explicaciones`)

### Qué problema había
1. Un tripulante no médico necesita entender qué es cada indicador, por qué se mide, cómo tomarse la medición correctamente y qué cambia en el espacio (`commit c9590f2`).
2. **Corrección de atribución (`commit 20590e3`):** al revisar los textos iniciales de hábitos de sueño y ánimo, se detectó que algunos consejos generales redactados por el equipo estaban colocados junto a enlaces de la NASA, dando a entender falsamente que la NASA decía eso.

### Cómo se solucionó (`commits c9590f2`, `20590e3`, `e143eb0`, `f8a3cec`)
En `backend/app/datos/explicaciones.json` y `backend/app/dominio/explicaciones.py` (`GET /api/explicaciones` y `GET /api/explicaciones/{clave}`):
- Cada indicador (incluyendo los nuevos `sueno_eficiencia_pct`, `sueno_despertares_min` basados en los estudios de actigrafía **ARCHeR** de la NASA, y `variabilidad_cardiaca` vinculada a la adaptación autonómica cardiovascular) explica en lenguaje sencillo: `que_es`, `por_que_se_mide`, `como_medirlo` y `en_el_espacio`.
- **Separación estricta entre lo que dice la NASA y los consejos generales:**
  - `medidas_nasa` y `senales_a_vigilar`: contienen **únicamente lo que dicen las páginas oficiales de la NASA**, incluyendo la **cita textual en inglés** (`cita_en`) y su enlace directo a `nasa.gov` (por ejemplo, hacer ejercicio de 6 a 7 días por semana con 1.5 horas de trabajo aeróbico/resistencia en la estación, o el uso de luces LED para el ritmo circadiano).
  - Donde la página oficial de la NASA no da una guía de medidas concretas para ese indicador (como en glucosa capilar, contramedidas directas de hipoxia o umbrales fijos de actigrafía/RMSSD), el sistema **lo declara abiertamente** en vez de inventar una recomendación oficial.
  - Los consejos prácticos de bienestar general llevan la etiqueta explícita `origen_habitos = "consejo_general_no_atribuido_a_nasa"`.

---

## 3. Entornos de Misión y Pérdida Ósea según la Gravedad (`/api/entornos`)

### Qué problema había
En el espacio, los astronautas pierden entre **1 % y 1.5 % de densidad mineral ósea por mes**. Sin embargo, esa cifra oficial de la NASA corresponde a misiones de **4 a 6 meses en microgravedad** (como en la Estación Espacial Internacional o en tránsito en una nave). Calcular esa misma pérdida ósea cuando la tripulación está en la superficie de la Luna o de Marte era un error conceptual, porque allí sí hay gravedad parcial y la propia NASA advierte que aún no hay datos suficientes para dar una tasa mensual en gravedad parcial.

### Cómo se solucionó (`commit 6598fc3`)
En `backend/app/datos/entornos.json` y `backend/app/dominio/entornos.py` (`GET /api/entornos` y `GET /api/entornos/{clave}`):
- Se definieron los 5 entornos operativos de la misión:
  - **En microgravedad (`nave` y `estacion`):** `estimacion_osea_aplica = true`, con la tasa de `1.0 % a 1.5 %` mensual limitada a un máximo de 6 meses y su cita oficial de la NASA.
  - **En gravedad parcial (`luna` con ~1/6 g, `marte` con ~3/8 g según la NASA, y `rover` en superficie):** `estimacion_osea_aplica = false`, explicando claramente el motivo y la fuente oficial para no mostrar cálculos óseos sin respaldo científico.
