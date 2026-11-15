# Documento Maestro del Proyecto y Estructura para Presentación (5 Diapositivas en Inglés)

Este documento reúne **toda la información actualizada de ORBIT Health** —incluyendo las últimas integraciones de **Nova** (compañía de apoyo emocional bilingüe con respiración guiada y memoria efímera), las **capas anatómicas realistas** (esqueleto, músculos y órganos), el **acceso con Tierra 3D** y los **4 perfiles de tripulación**— y, en la segunda mitad, te entrega **las 5 diapositivas listas en inglés** (títulos, bullets cortos para pantalla, qué visual poner y qué decir en cada una en un pitch de 3 minutos).

---

# PARTE 1 — Resumen Completo del Proyecto (Contexto en Español)

## 1. ¿De qué trata ORBIT Health?
**ORBIT Health** es una plataforma autónoma de monitoreo clínico, triaje médico, vigilancia ambiental de cabina y acompañamiento psicológico diseñada para **misiones espaciales de larga duración (Luna y Marte)** donde **no hay internet y no viaja un médico a bordo**.

Su objetivo es dar a una tripulación pequeña (4 a 6 astronautas: un único comandante y tripulantes especialistas) **capacidad de decisión médica inmediata, explicable y privada dentro de la nave**, mientras resguarda, compacta y prioriza la telemetría que se enviará al control médico en la Tierra cuando vuelva la ventana de comunicación.

---

## 2. La Problemática Principal (¿Por qué falla el modelo actual lejos de la Tierra?)

En la Estación Espacial Internacional (órbita baja), si un astronauta se enferma, habla en tiempo real con médicos en la Tierra y puede ser evacuado en horas. **Camino a Marte, ese modelo se rompe por 3 razones críticas:**

1. **Retardo extremo y apagones de señal (Incomunicación):**
   - La señal de radio hacia Marte tarda hasta **22 minutos por sentido** (más de **40 minutos** para recibir una respuesta), sumado a eclipses o conjunciones solares donde la nave queda **días sin conexión**. En una emergencia médica aguda, esperar a la Tierra no es opción.
2. **Sin médico a bordo, alarmas genéricas y riesgo ambiental compartido:**
   - Todos a bordo son astronautas, no médicos de urgencias.
   - Los monitores tradicionales usan límites genéricos (cuando la alarma suena, el tripulante ya está grave) o dan falsas alarmas por movimientos del reloj. Además, si el dióxido de carbono ($\text{CO}_2$) sube o el oxígeno ($\text{O}_2$) baja en la cabina, varios tripulantes tendrán síntomas al mismo tiempo: tratarlos por separado como enfermedades individuales hace perder minutos vitales para reparar el soporte vital de la nave.
3. **Aislamiento psicológico y desconfianza en el encierro:**
   - Meses de aislamiento y alteraciones del sueño afectan el ánimo y la cognición. Pero si el astronauta sabe que su diario, su ánimo o lo que platica se envía a la Tierra o lo lee su comandante sin permiso, **oculta lo que siente y deja de pedir ayuda**.

---

## 3. ¿Cómo lo resuelve ORBIT Health? (Las Integraciones Clave del Sistema)

### A. Triaje Clínico Autónomo, Línea Base Personal de 14 Días y Capas Anatómicas Realistas
- Combina la escala internacional de urgencias **NEWS2** (6 signos vitales) con indicadores espaciales: dosis de radiación, eficiencia y despertares de sueño (actigrafía tipo ARCHeR), variabilidad cardíaca (HRV por RMSSD), presión diastólica y glucosa.
- **Línea base personal de 14 días:** compara cada lectura contra el propio historial de 14 días de ese astronauta (usando estadística robusta que no se altera con valores extremos), detectando deterioros silenciosos en **amarillo** antes de que sean críticos.
- **Visualización anatómica realista por capas:** proyecta el estado clínico sobre láminas anatómicas alineadas de **esqueleto, músculos y órganos** (cerebro, ojos, corazón, pulmones, hígado, estómago, intestinos) y adapta las explicaciones según la gravedad del entorno (Tierra, Órbita ISS, Luna, Marte o Rover).
- **Filtro de artefactos de banda Bluetooth:** agrupa las muestras en ventanas de 60 segundos usando la **mediana**, absorbiendo golpes o sacudidas de muñeca sin disparar falsas alarmas.

### B. Cruce de Salud Humana con el Ambiente de la Cabina (Alerta Colectiva)
- Monitorea continuamente la cabina ($\text{CO}_2$, $\text{O}_2$, presión, temperatura, humedad y radiación) y la cruza con los signos de toda la tripulación.
- Si el $\text{CO}_2$ sube o el $\text{O}_2$ cae y **dos o más tripulantes** presentan signos alterados en la misma ventana de 30 minutos, ORBIT lanza una **Alerta Ambiental Colectiva** para que la tripulación revise los filtros de aire y el soporte vital de inmediato.

### C. "Nova": Compañía de Apoyo Bilingüe (ES/EN), Respiración Guiada y Guardia de IA
- **Cero cajas negras en decisiones médicas:** el semáforo (`verde`, `amarillo`, `rojo`) y los pasos clínicos los calculan reglas deterministas, adaptadas al tono (`directo` o `calido`) y detalle (`breve` o `completo`) que prefiere cada astronauta (`Valeria Montoya`, `Mateo Ríos`, `Camila Ortega` y `Andrés Leal`).
- **Nova (Voz y Chat en Español e Inglés 100 % offline):**
  - Saluda al instante a cada astronauta por su nombre y sus intereses (`GET /api/asistente/saludo/{tid}`) y ofrece atajos rápidos (*"Me siento solo"*, *"Estoy estresado"*, *"No puedo dormir"*, *"Quiero respirar"*).
  - **Respiración guiada determinista:** ante *"Quiero respirar"*, guía un ejercicio escrito y validado (**inhalar 4 s, sostener y exhalar 6 s**) sin pasar por el modelo de IA.
  - **Perfil privado (`intereses` y `rasgos`) y memoria corta sin rastro:** recuerda los últimos 6 mensajes de la plática sin guardarlos jamás en la base de datos del servidor y sin enviarlos nunca a proveedores externos.
  - **Precalentamiento en CPU (`ORBIT_PRECALENTAR=1`):** carga el modelo local y el motor de voz al arrancar para responder en ~1–4 segundos.
- **Guardia de IA bilingüe, saneado de prompt y límites de uso:** limpia caracteres invisibles o intentos de inyección (`sanear_para_prompt`), aplica límites por minuto y concurrencia (`limites.py`) e inspecciona cada respuesta del modelo en español e inglés. Si intenta filtrar sus instrucciones internas, inventar un número que no está en el estado clínico, mencionar un fármaco o ignorar una crisis emocional, **descarta la respuesta al instante** y entrega el protocolo médico escrito. Si en modo demo con internet se usa respaldo en la nube, **jamás se envían el nombre, intereses, rasgos ni conversación del astronauta**.

### D. Bienestar Psicológico Privado y Protocolo de Crisis Cruzado con Oxígeno
- **Privacidad por diseño:** el diario personal, el ánimo diario, los tamizajes PHQ-2 y el perfil de Nova **jamás salen hacia la Tierra** ni pueden ser vistos por el comandante ni por otros compañeros.
- **Protocolo de Crisis inteligente (ES/EN):** si un tripulante reporta una crisis emocional, ORBIT primero **verifica el oxígeno de la cabina** (porque la hipoxia en el espacio causa ansiedad y confusión aguda) y muestra pasos de seguridad que nunca se recortan.
- **Aviso consentido y revocable al comandante:** el tripulante puede pedir apoyo al comandante con un clic sin exponer su diario, y puede **revocar ese aviso en cualquier momento**.

### E. Enlace Resiliente Tierra-Espacio, Autocuración y Ciencia NASA HRP
- **Cola offline con cadena criptográfica (`SHA-256`) y base de datos que se repara sola:** durante un apagón o eclipse, ningún evento se pierde; si hay un corte de energía que dañe la base de datos, el sistema respalda la evidencia y se restaura solo al arrancar.
- **Compactación inteligente y prioridad roja:** al reconectar con la Tierra, **compacta cientos de lecturas verdes rutinarias en un solo resumen** y envía primero las **emergencias rojas**, calculando el retardo real de la luz (ISS, Luna o Marte).
- **Alineación científica NASA HRP y Despliegue Listo (PWA + Ejecutable de Doble Clic + Docker + Auditoría):** mapea los **5 peligros (`Hazards`) y 17 riesgos del Programa de Investigación Humana de la NASA** (`NASA-STD-3001`), funciona como **aplicación instalable (PWA)** que nunca guarda datos clínicos viejos en caché del navegador, puede correr como **ejecutable autónomo de doble clic** sin instalar Python ni Node (`lanzador.py`), incluye contenedor Docker sin privilegios y un script de auditoría automática de seguridad (`auditoria_seguridad.py`).

---
---

# PARTE 2 — Las 5 Diapositivas en Inglés (Listas para Presentar en 3 Minutos)

> **Consejo para tus diapositivas:** Copia en cada slide únicamente los puntos bajo **On-Slide Text** (breves, limpios y fáciles de escanear por los jueces) y usa las **Speaker Notes** como tu guion hablado en inglés.

---

## Slide 1: Title & The 40-Minute Silence Hook (`0:00 – 0:30`)
**Propósito:** Captar la atención de los jueces con el escenario real camino a Marte sin médico a bordo y presentar **ORBIT Health**.

### Texto en la diapositiva (On-Slide Text)
- **Title:** **ORBIT Health**
- **Subtitle:** Autonomous Clinical Triage, Cabin Correlation & Private Crew Wellness for Deep-Space Missions
- **3 Core Realities of Deep Space:**
  - **40+ Min Silence:** Round-trip radio delay to Mars + multi-day solar blackouts
  - **0 Onboard Doctors:** Crewmates must triage and act autonomously
  - **100% Offline & Self-Healing:** Zero cloud dependency, built for spacecraft hardware

### Qué mostrar visualmente (Visual)
- Pantalla de inicio con la **Tierra 3D interactiva** junto al tablero principal del **Monitor** mostrando al astronauta y sus capas anatómicas (esqueleto, músculos y órganos).

### Qué decir en inglés (Speaker Notes)
> *"Imagine you are halfway to Mars. There is no doctor on board. Suddenly, a crewmate starts breathing rapidly, feels dizzy, and their blood oxygen drops. You radio Mission Control on Earth—but your voice takes 20 minutes to arrive, and their answer takes another 20 minutes to come back. In emergency medicine, 40 minutes of silence is the difference between a close call and a tragedy. That is why we built **ORBIT Health**: an autonomous medical copilot that lives 100% inside the spacecraft, with zero internet dependency."*

---

## Slide 2: The Problem — Why Earth-Based Telemedicine Fails Beyond Low-Earth Orbit (`0:30 – 1:05`)
**Propósito:** Explicar de forma directa los 3 problemas que hoy ponen en peligro a una tripulación en la Luna o Marte.

### Texto en la diapositiva (On-Slide Text)
- **Title:** **Why Current Space Telemedicine Breaks on the Way to Mars**
- **1. Communication Blackouts & Delays:** Up to 44-minute round-trip latency and solar conjunction blackouts make real-time Earth triage impossible.
- **2. Generic Alarms & Blindness to Cabin Air:** Fixed population thresholds react too late, and they treat shared habitat poisoning ($\text{CO}_2$ spike / low $\text{O}_2$) as isolated individual illnesses.
- **3. The Confinement Privacy Paradox:** Isolation impacts mental health, but astronauts hide symptoms if their private journal or mood is sent to Earth or visible to their commander without consent.

### Qué mostrar visualmente (Visual)
- Tres tarjetas visuales claras (1. Antena en eclipse / 2. Alerta de aire en cabina / 3. Candado de privacidad mental) o la vista de Comparativa *"With ORBIT vs Without ORBIT"*.

### Qué decir en inglés (Speaker Notes)
> *"Today, deep-space healthcare faces three critical bottlenecks. First: communication delays and solar blackouts leave the crew isolated for hours or days. Second: generic medical alarms don't know each astronaut's body, and if two crewmates get sick at the same time, it might not be an illness—it might be toxic cabin air. And third: mental health in confinement. If astronauts feel their private thoughts or mood are sent to Earth or to their commander without permission, they simply stop asking for help."*

---

## Slide 3: Autonomous Clinical Triage, Realistic Anatomy & Collective Cabin Alerts (`1:05 – 1:50`)
**Propósito:** Mostrar cómo el motor clínico detecta antes con la línea base de 14 días, proyecta sobre capas anatómicas realistas, filtra golpes del reloj y cruza con el aire de la nave.

### Texto en la diapositiva (On-Slide Text)
- **Title:** **Early Detection: 14-Day Personal Baseline, Realistic Anatomy & Cabin Correlation**
- **Dual Clinical Engine:** Combines **NEWS2** emergency scoring with radiation dose, sleep efficiency (ARCHeR actigraphy), HRV recovery (RMSSD), blood pressure, and glucose.
- **14-Day Personal Baseline & Artifact Filtering:** Detects subtle deviations in **Yellow** against each astronaut's own 14-day history while 60-second median windows filter out Bluetooth wristband motion spikes.
- **Realistic Anatomical Layers:** Maps clinical findings across **Skeleton, Muscle, and Organ layers** adapted to gravity environments (ISS, Moon, Mars).
- **Collective Habitat Alert:** Automatically cross-checks crew vitals with cabin $\text{CO}_2$ and $\text{O}_2$—triggering a collective life-support alert when 2+ crewmates are affected within 30 minutes.

### Qué mostrar visualmente (Visual)
- Vista del **Monitor** con las láminas realistas de **Esqueleto / Músculos / Órganos**, el reloj 3D de la **Banda** y el banner de **Alerta Ambiental Colectiva**.

### Qué decir en inglés (Speaker Notes)
> *"How does ORBIT Health solve this? First, instead of waiting for an astronaut to cross a dangerous generic limit, our dual engine learns what is normal for each person over a rolling 14-day baseline. It maps vital signs, radiation, sleep, and heart recovery directly onto realistic skeleton, muscle, and organ layers, while 60-second median windows filter out false wrist bumps from Bluetooth bands. Second, we connect the crew with the spacecraft: if cabin carbon dioxide rises or oxygen drops and two or more crewmates show symptoms within 30 minutes, ORBIT triggers a Collective Cabin Alert so they fix life support immediately."*

---

## Slide 4: Private Mental Wellness & "Nova" — Our Guarded Bilingual Companion (`1:50 – 2:30`)
**Propósito:** Destacar la privacidad absoluta, la nueva compañía **Nova** (voz y chat bilingüe con respiración guiada y Guardia de IA) y el protocolo de crisis cruzado con oxígeno.

### Texto en la diapositiva (On-Slide Text)
- **Title:** **Zero Black Boxes: Private Wellness & "Nova" Bilingual Companion**
- **100% Private by Design:** Journals, daily mood, PHQ-2 screenings, and personal profiles **never leave the ship** and cannot be opened by the commander.
- **Meet "Nova" (Offline ES/EN Voice & Text Companion):**
  - Greets each astronaut by name, remembers their Earth motivators and personality traits, keeps a 6-turn ephemeral memory (never stored on disk), and guides **4–6s breathing exercises**.
  - Protected by a **Deterministic AI Safety Guard** that blocks hallucinated numbers, medications, or unsafe advice.
- **Hypoxia-Aware Crisis Protocol:** Verifies cabin $\text{O}_2$ first during emotional crises (since hypoxia mimics acute anxiety) and enables **one-click revocable consent** to notify the commander.

### Qué mostrar visualmente (Visual)
- Vista de la pestaña **Asistente (Nova)** mostrando las burbujas de conversación, los atajos (*"Quiero respirar"* / *"I want to breathe"*), el botón de voz y la tarjeta del **Protocolo de Crisis con consentimiento revocable**.

### Qué decir en inglés (Speaker Notes)
> *"Third, we protect the crew's mind with zero black boxes and total privacy. AI never makes clinical decisions—deterministic rules do. And because there is no doctor on board, each astronaut has **Nova**, an offline English and Spanish voice and text companion. Nova greets them by name, remembers what motivates them on Earth without storing chat logs on the server, guides their breathing, and passes every word through a deterministic AI Guard so it never invents a number or prescribes medication. If a crewmate enters an emotional crisis, ORBIT checks cabin oxygen first—because hypoxia causes acute anxiety—and lets them alert the commander only with revocable consent."*

---

## Slide 5: Blackout-Resilient Sync, NASA HRP Traceability & Closing (`2:30 – 3:00`)
**Propósito:** Cerrar con fuerza mostrando cómo funciona el Modo Eclipse, la compactación hacia la Tierra, el rigor científico con la NASA y la frase final.

### Texto en la diapositiva (On-Slide Text)
- **Title:** **Blackout-Resilient Earth Sync & NASA HRP Scientific Alignment**
- **Tamper-Evident Offline Queue & Self-Healing DB:** Seals every event in a **SHA-256 hash chain** during blackouts and automatically recovers from power-loss corruption.
- **Smart Reconnection & Routine Compaction:** Compacts hundreds of routine green readings into a single summary and transmits **Red Emergencies first**, calculating real light-time delay (ISS, Moon, Mars).
- **Grounded in NASA Science:** Directly maps all **5 NASA HRP Hazards and 17 Risks** (`NASA-STD-3001`), transparently declaring clinical validation boundaries.
- **Takeaway:** *"When Earth is 40 minutes away, astronauts don't need a radio miracle—they need clear, private, and trustworthy answers on board."*

### Qué mostrar visualmente (Visual)
- Consola de **Enlace en Modo Eclipse / Marte** (mostrando la compactación y prioridad 1 roja) junto a la vista de los **5 Peligros de la NASA**.

### Qué decir en inglés (Speaker Notes)
> *"And what happens during a communication blackout? Nothing is lost. ORBIT seals every event in a tamper-evident digital chain. When signal returns, it compacts hundreds of routine green readings into a single summary and transmits Red emergencies first, so doctors on Earth see what is urgent in the very first second. Everything in ORBIT is mapped to NASA's 5 Hazards and 17 Human Research Program risks, citing NASA-STD-3001 directly. Because when Earth is 40 minutes away, astronauts cannot wait for a miracle over the radio—they need clear, private, and safe answers right on board. That is **ORBIT Health**. Thank you."*

---

> **Firma de IA y Justificación / AI Signature & Justification (SI Disclosure):**
> - **Herramienta utilizada / Tool used:** **Antigravity (Google DeepMind)** sobre base técnica documentada con **Claude (Anthropic / Claude Code)**.
> - **Justificación / Justification:** Se utilizó para organizar el resumen ejecutivo del proyecto y estructurar el contenido en inglés para la presentación de 5 diapositivas a partir de las decisiones e implementación del equipo humano. / *Used to synthesize the executive project summary and structure the 5-slide English presentation content based on the human team's design and implementation (in compliance with NASA Space Apps Challenge rules).*
