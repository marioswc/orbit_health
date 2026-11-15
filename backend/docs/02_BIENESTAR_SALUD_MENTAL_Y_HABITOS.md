# 02 — Bienestar, Salud Mental, Crisis y Hábitos

En una misión espacial prolongada, el aislamiento, el encierro y las alteraciones del aire dentro de la nave afectan directamente el bienestar mental. Este módulo resuelve cómo dar apoyo psicológico y seguimiento de hábitos **protegiendo al máximo la intimidad de cada tripulante**.

---

## 1. Privacidad Blindada: Diario, Ánimo Diario y Tamizaje PHQ-2

### Qué problema había
Si un tripulante siente que lo que escribe en su diario o cómo se siente de ánimo va a enviarse automáticamente al control en Tierra o lo va a leer el comandante sin su permiso, dejará de usar la herramienta.

### Cómo se solucionó (`commits f0a7fe8`, `ea13926`, `ce1e339`)
- **Aislamiento por diseño en la base de datos (`backend/app/repositorios/schema.sql`):** las tablas `diario_privado`, `animo_diario` (escala de 1 a 5) y `tamizajes` (cuestionario PHQ-2) **no tienen ninguna conexión con la cola de salida hacia Tierra (`cola_salida`)** ni con los informes exportables (`/api/informe`).
- **Acceso exclusivo del dueño:** en `backend/app/api/bienestar.py`, las rutas `GET /api/diario/{tid}`, `POST /api/diario`, `GET /api/animo/{tid}`, `POST /api/animo` y `POST /api/tamizajes` comprueban que quien consulta sea **únicamente el propio tripulante**. Ni el médico ni el comandante pueden abrir el diario o el ánimo de otra persona.

---

## 2. Protocolo de Crisis Psicológica Cruzado con el Oxígeno de Cabina

### Qué problema había
Un cuestionario PHQ-2 básico solo daba un puntaje de 0 a 6 y mostraba cápsulas de lectura, pero no tenía un protocolo claro si alguien reportaba **riesgo de autolesión o crisis aguda**. Además, en medicina aeroespacial existe un factor crítico: cuando baja el oxígeno o se altera el aire en una cabina cerrada, el cerebro sufre síntomas inmediatos (angustia severa, confusión, irritabilidad o alteración del juicio) que parecen una crisis puramente psicológica pero tienen una causa ambiental urgente.

### Cómo se solucionó (`commit ce363f8`)
En `backend/app/dominio/crisis.py` y `backend/app/servicios/bienestar.py` se construyó un protocolo determinista en tres niveles (`ninguno`, `seguimiento`, `crisis`):
1. **Cruce automático con el oxígeno de cabina (`o2_cabina`):**
   - Al evaluar un tamizaje (`POST /api/tamizajes`) o consultar el protocolo (`GET /api/crisis/protocolo`), el sistema revisa la calidad de oxígeno indicada o busca la última lectura de `o2_cabina` registrada en la nave.
   - Si el oxígeno de la cabina está alterado, el **primer paso obligatorio** del protocolo ordena verificar el oxígeno ambiental y medir la SpO₂ del tripulante, explicando que el aire de la nave puede estar provocando o agravando la crisis.
2. **Pasos de seguridad que nunca se recortan:**
   - En nivel de `crisis` (por riesgo de autolesión o falta severa de oxígeno en cabina), el protocolo guía al tripulante para no quedarse a solas, acudir a un módulo común, alejarse de herramientas o medicamentos riesgosos y aplicar respiración controlada (4-6 s) y anclaje sensorial (5-4-3-2-1).
   - Aunque el tripulante haya configurado la interfaz en modo "breve", los pasos de seguridad de una crisis se marcan como esenciales y **jamás se ocultan ni se resumen**.

---

## 3. Aviso Consentido y Revocable al Médico de a Bordo

### Qué problema había
Mantener la privacidad total es indispensable, pero si un tripulante está pasando por una crisis o un tamizaje positivo y **quiere pedir ayuda** al médico de la tripulación sin tener que explicarlo todo en voz alta ni enviar nada a Tierra, necesitaba un canal interno seguro.

### Cómo se solucionó (`commit ce363f8`)
Se creó la tabla `avisos_salud_mental` y un flujo de consentimiento explícito:
- **Envío voluntario (`POST /api/crisis/aviso-medico`):** solo el propio tripulante puede enviarlo, marcando `consentimiento=True`. El aviso notifica al médico/comandante que el tripulante solicita acompañamiento (con un mensaje corto opcional), pero **sin adjuntar su diario privado ni su historial de ánimo**, y **sin salir jamás hacia Tierra**.
- **Revocación instantánea (`POST /api/crisis/avisos/{aviso_id}/revocar`):** si el tripulante cambia de opinión, puede revocar su consentimiento en cualquier momento. En ese instante, el aviso desaparece de la bandeja del médico (`GET /api/crisis/avisos`).
- **Atención y trazabilidad (`POST /api/crisis/avisos/{aviso_id}/atender` y `GET /api/crisis/avisos/{tid}`):** el tripulante puede ver en todo momento el estado de los avisos que compartió (`pendiente`, `atendido` o `revocado`), y cada acción queda registrada en la auditoría interna.

---

## 4. Asistente Adaptable por Preferencias del Tripulante

### Qué problema había
En situaciones de estrés o fatiga, hay personas que prefieren instrucciones cortas y al grano, mientras que otras prefieren un trato más cálido y explicaciones completas. Sin embargo, usar un modelo de inteligencia artificial que "adivine" el humor del tripulante leyendo su diario violaría su privacidad y sería impredecible.

### Cómo se solucionó (`commit c21bffa`)
En `backend/app/dominio/acciones.py` y `backend/app/servicios/preferencias.py` (`GET /api/preferencias/{tid}` y `PUT /api/preferencias/{tid}`):
- **El propio tripulante elige cómo quiere que le hablen:**
  - **Tono:** `directo` (instrucciones concisas y operativas) o `calido` (lenguaje cercano y empático).
  - **Detalle:** `breve` (solo pasos esenciales) o `completo` (incluye contexto adicional).
  - **Frecuencia de recordatorios:** `normal`, `frecuente` o `minimo`.
- **Reglas de oro de seguridad:**
  1. Cambiar el estilo **nunca altera el nivel clínico (verde/amarillo/rojo) ni la prioridad en la cola a Tierra**.
  2. Elegir recordatorios en `minimo` **nunca alarga los tiempos cuando el tripulante está en alerta roja** (una emergencia siempre pide medición cada 5 minutos).
  3. **Se adapta a quien mira la pantalla:** si el tripulante T2 está atendiendo a un compañero incapacitado (T1), las instrucciones se muestran con el estilo que eligió T2, que es quien está leyendo y actuando.
  4. **No espía el diario ni el ánimo:** una prueba automática verifica que escribir en el diario o registrar ánimo bajo no modifica silenciosamente las preferencias ni las respuestas clínicas.

---

## 5. Recordatorios de Medición y Racha Diaria sin Presión

### Recordatorios inteligentes (`commit ac9b1b6`)
- Las rutas `GET /api/recordatorios` y `GET /api/recordatorios/{tid}` (`backend/app/servicios/recordatorios.py`) calculan si a un tripulante ya le toca medirse según su nivel actual (60, 15 o 5 min) y su preferencia elegida.
- Ordena la lista poniendo primero a quien lleva más tiempo atrasado e ignora los datos precargados de calibración para no fingir que el tripulante se acaba de medir.

### Racha de mediciones (`commit 1173cc0`)
- La ruta `GET /api/racha/{tid}` (`backend/app/servicios/racha.py`) ofrece una motivación ligera para mantener el hábito de registrarse:
  - Un día cuenta como completo cuando el tripulante registra sus **5 signos vitales cuantitativos** (frecuencia cardíaca, frecuencia respiratoria, SpO₂, presión sistólica y temperatura).
  - **Sin presión ni castigos:** mientras el día de hoy sigue en curso y aún no se completan los 5 signos, la racha acumulada hasta ayer **no se rompe**. Solo entrega 3 reconocimientos sencillos (`primer_dia`, `tres_dias`, `siete_dias`).
