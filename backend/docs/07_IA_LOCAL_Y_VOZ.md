# 07 — IA Local Explicativa, Voz Offline, Asistente Personal Bilingüe y Guardia de IA

Este módulo incorpora capacidades opcionales de **Inteligencia Artificial local**, **asistente personal por texto y voz (`push-to-talk`) en español e inglés** y un **perfil privado de intereses y rasgos**, pensadas para asistir a la tripulación cuando tiene las manos ocupadas o necesita acompañamiento en misiones largas, **sin romper nunca el principio de que las decisiones médicas las toman reglas deterministas**.

Para detalles adicionales de política y límites puedes consultar también [IA_LOCAL.md](../../docs/IA_LOCAL.md).

---

## 1. Explicador con IA Local y Adaptación al Estilo (`GET /api/estado/{tid}/explicacion`)

### Qué problema había
Un tripulante puede querer una explicación redactada en lenguaje natural sobre por qué su estado general está en verde, amarillo o rojo y qué señales influyeron. Sin embargo, usar un modelo de inteligencia artificial en medicina espacial tiene cuatro riesgos graves:
1. Que el modelo "alucine" un diagnóstico, invente valores o cambie el nivel de una emergencia.
2. Que ignore el estilo preferido del astronauta (por ejemplo, dar un texto largo cuando pidió respuestas breves y directas durante una maniobra).
3. Que un modelo pequeño en la computadora de la nave consuma demasiado procesador generando textos interminables.
4. Que el servidor de IA no esté encendido o tarde demasiado y deje al tripulante sin respuesta.

### Cómo se solucionó (`commits 252366a`, `a1129ef`, `b7c887a`, `b7f8d68`)
En `backend/app/api/asistente.py` y `backend/app/servicios/explicador_local.py`:
- **La IA solo explica, nunca decide:** primero el motor clínico determinista calcula el estado (`servicio_estado.estado_tripulante`). El modelo recibe únicamente ese resultado ya calculado con instrucciones estrictas de resumirlo en español sin diagnosticar, sin recetar medicamentos y recordando que las acciones procedimentales tienen prioridad. El campo `nivel_general` que devuelve la ruta es siempre el del motor clínico intacto.
- **Adaptación automática a `tono` y `detalle` (`commit b7c887a`):** la ruta lee las preferencias guardadas del tripulante (`tono`: `directo` o `calido`; `detalle`: `breve` o `completo`) y ajusta tanto las instrucciones al modelo (45 palabras en modo breve vs 95 en completo) como el respaldo determinista (`_fallback`), que en modo cálido incluye un mensaje de acompañamiento y en modo breve se reduce a una sola línea concisa.
- **Tope de 220 tokens para cuidar el procesador (`commit b7f8d68`):** `consultar_modelo` limita la generación a un máximo de `220` tokens (`num_predict` en Ollama / `max_tokens` en OpenAI-compatible) para que modelos locales ligeros (`qwen2.5:1.5b` o `0.5b`) respondan rápido en CPU sin saturar la estación.
- **Candado contra redirecciones (`_url_local` y `_SinRedireccion`):** verifica que `ORBIT_IA_LOCAL_URL` apunte exclusivamente a `localhost`, `127.0.0.1` o `::1` y **prohíbe seguir redirecciones HTTP (`301`/`302`/`307`)**, impidiendo que un puerto local desvíe la consulta hacia otro servidor.
- **Respaldo instantáneo por reglas (`_fallback`):** si no se configuró un modelo, o si tarda más de `ORBIT_IA_LOCAL_TIMEOUT_S`, falla o su texto es rechazado por la Guardia de IA, el sistema responde automáticamente con la explicación determinista (`fuente: "reglas_locales"`, `generado_por_ia: False`).

---

## 2. Perfil Privado (`intereses` y `rasgos`) y Chat por Texto (`perfil_ia.py`)

### Qué problema había
En una misión de meses o años lejos de la Tierra y sin médico a bordo, el aislamiento pesa. Los astronautas querían que su asistente pudiera hablarles por su nombre, recordar qué los motiva en Tierra (`intereses`) y cómo son en sus propias palabras (`rasgos`), además de poder escribirle por texto cuando no quieren hablar en voz alta. Pero esos datos son íntimos: **no deben ser visibles para el comandante ni para otros compañeros, y jamás deben enviarse a un proveedor externo en internet**.

### Cómo se solucionó (`commits 3730ff7`, `851e767`, `d824017`, `16f3b2a`)
Se crearon `backend/app/api/perfil_ia.py`, `backend/app/servicios/perfil_ia.py`, `backend/app/repositorios/perfil_ia.py` y la tabla `perfil_ia` en `schema.sql` (con migración automática en `conexion.py` para añadir la columna `rasgos` a bases existentes):
1. **Perfil privado de intereses y rasgos (`GET /api/perfil-ia/{tid}` y `PUT /api/perfil-ia/{tid}`):**
   - Permite a cada tripulante guardar hasta 160 caracteres para sus `intereses` (qué le gusta y motiva) y hasta 160 caracteres para sus `rasgos` (cómo es y cómo prefiere que lo acompañen), pudiendo actualizarlos juntos o por separado.
   - Los 4 astronautas ficticios (`Valeria Montoya`, `Mateo Ríos`, `Camila Ortega` y `Andrés Leal`) traen perfiles sembrados de demostración en `semilla.py`, respetando siempre cualquier cambio que el usuario ya haya guardado.
   - **Privacidad absoluta (`exigir_propietario`):** tanto leer como modificar este perfil exige que el usuario autenticado sea **exactamente el dueño (`actor.id == tid`)**. Ni siquiera el comandante ni otro compañero pueden consultarlo (`403`).
   - **Nunca sale de la estación:** ni `intereses` ni `rasgos` se incluyen jamás en la cola hacia Tierra ni en los paquetes firmados, y **solo se pasan al modelo cuando el proveedor es `local`** (con DeepSeek no se envían).
2. **Toque personal determinista en español e inglés (`_toque_personal` en `voz_local.py`):**
   - El asistente saluda al astronauta por su **nombre** y, si tiene intereses guardados, genera un recordatorio empático determinista en el idioma de la conversación (`es` o `en`) y adaptado a su `tono` (`directo` o `calido`). Así el astronauta recibe un trato cercano incluso cuando el modelo de IA está apagado o su respuesta es reemplazada por el respaldo seguro.
3. **Chat escrito bilingüe con el asistente (`POST /api/asistente/chat/{tid}`):**
   - Permite conversar por texto (en español o inglés, detectando el idioma automáticamente con `guardia_ia.detectar_idioma` o recibiendo `idioma: "es" | "en"`) con las mismas garantías de la Guardia de IA y sin necesidad de micrófono. Es también **exclusivo del propio tripulante**.

---

## 3. Conversación por Voz Bilingüe (`POST /api/voz/chat/{tid}`) e Instaladores Offline

### Qué problema había
Durante un procedimiento a bordo, un astronauta puede necesitar preguntar en voz alta por su estado (en español o en inglés) sin usar el teclado. Para lograrlo sin red y en una computadora de estación espacial, había que resolver:
1. Cómo transcribir la voz, detectar el idioma, generar la respuesta y hablarla de vuelta **sin internet y sin guardar grabaciones privadas en la base de datos**.
2. Cómo evitar que un archivo de audio dañado o corrupto provoque un error interno no controlado (`500`).
3. Cómo evitar que un audio enorme o varias peticiones de voz al mismo tiempo saturen el procesador (CPU) y la memoria de la nave.

### Cómo se solucionó (`commits 252366a`, `5edee80`, `a1129ef`, `300bcfc`, `1a71dbf`, `851e767`, `38f86f4`, `30a9244`)
En `backend/app/api/voz.py`, `backend/app/servicios/voz_local.py` y `scripts/`:

1. **Privacidad por dueño (`commit 851e767`):**
   - `POST /api/voz/chat/{tid}` verifica que quien habla sea el propio tripulante (`actor.id == tid`).
2. **Flujo de voz en 3 pasos 100 % local, bilingüe (`es`/`en`) y sin rastro en base de datos:**
   - **Escuchar y detectar idioma (`transcribir_con_idioma`, `commit 30a9244`):** recibe audio crudo (`.wav`, `.webm`, `.ogg`, `.mp3`, `.m4a`) y lo transcribe localmente usando `faster-whisper` (`compute_type="int8"`), detectando automáticamente si el astronauta habló en **español (`es`) o inglés (`en`)**. El archivo temporal se borra inmediatamente en un bloque `finally` y **jamás se guarda en SQLite ni entra a la cola de Tierra**.
   - **Validación limpia de audio corrupto (`commit 38f86f4`):** si llega un archivo truncado o inválido que no puede decodificarse, devuelve un `422` claro (*"El archivo de audio no es válido o no pudo decodificarse"*).
   - **Pensar y Hablar en el mismo idioma (`sintetizar`):** responde en el idioma detectado y sintetiza el audio WAV (`base64`) usando `piper` con la voz española (`ORBIT_VOZ_PIPER_MODELO`) o la voz inglesa (`ORBIT_VOZ_PIPER_MODELO_EN`, usando la española como respaldo si la segunda no está configurada).
3. **Bloqueo de descargas externas y protección de CPU (`commit 5edee80`):**
   - `ORBIT_VOZ_STT_LOCAL_ONLY=1` exige que el modelo de Whisper ya exista en disco (`local_files_only=True`).
   - Valida el tamaño máximo de audio (`ORBIT_VOZ_MAX_AUDIO_BYTES`, 10 MB por defecto, devolviendo `413` si se excede), recorta la respuesta a **600 caracteres** antes de sintetizarla y usa un semáforo (`_TRABAJO_VOZ = BoundedSemaphore(1)`) que permite **una sola inferencia de voz activa a la vez** (`429` si está ocupada).
4. **Scripts de aprovisionamiento previo al vuelo (`commits 300bcfc`, `1a71dbf`, `30a9244`):**
   - `scripts/instalar_ia_local.sh`: instala Ollama en `~/.local/bin` **sin `sudo`**, verifica su huella SHA-256 oficial y descarga el modelo ligero (`qwen2.5:1.5b`).
   - `scripts/instalar_voz_local.sh`: descarga en `backend/models/` el modelo `faster-whisper` (`small`, `int8`) y las dos voces de `piper` (**español de México** `es_MX-claude-high.onnx` e **inglés de EE. UU.** `en_US-lessac-medium.onnx`) para operar 100 % sin red.

---

## 4. Transparencia en Modo Demo con Proveedor Externo Opcional (DeepSeek)

### Qué problema había
En el espacio profundo toda la IA debe correr 100 % local (`Ollama`). Sin embargo, durante demostraciones en Tierra en computadoras sin recursos suficientes para correr un modelo local pero con internet, el equipo necesitaba la opción de conectar un proveedor externo (DeepSeek) **sin engañar a los jueces ni exponer jamás datos íntimos o situaciones de crisis**.

### Cómo se solucionó (`commits 507c8aa`, `f59636e`, `6bbf301`, `16f3b2a`)
En `backend/app/servicios/explicador_local.py` y `backend/app/servicios/voz_local.py`:
- **Desactivado por defecto en modo vuelo:** solo se habilita si se configura `ORBIT_DEEPSEEK_API_KEY` (y `ORBIT_IA_PROVEEDOR=deepseek` o `auto`). Si se define `ORBIT_IA_PROVEEDOR=local`, opera exclusivamente en `localhost`.
- **Etiquetado honesto y aviso explícito de salida de datos:** cuando una respuesta proviene de DeepSeek, reporta `fuente: "deepseek"` y advierte en `aviso`: *"Texto generado por proveedor externo (DeepSeek); datos del estado salieron de la estación. En vuelo usar ORBIT_IA_PROVEEDOR=local"*.
- **Protección de datos sensibles incluso en demo:**
  - Los **`intereses` y `rasgos` (`perfil_ia`) jamás se envían a DeepSeek**; solo se inyectan cuando el proveedor es `local`.
  - Si un tripulante expresa una **crisis emocional**, `detectar_crisis` corta el flujo **antes** de hacer cualquier llamada de red.
  - La respuesta de DeepSeek pasa exactamente por la misma **Guardia de IA (`validar_respuesta`)** que el modelo local.

---

## 5. Guardia de IA Bilingüe: Detección de Crisis y Validación Estricta (`guardia_ia.py`)

### Qué problema había
Confiar únicamente en las instrucciones del *prompt* no basta en un entorno médico: un modelo puede equivocarse, inventar una cifra, sugerir tomar un analgésico (en español o en inglés) o ser manipulado mediante *prompt injection*. Y **si un tripulante expresa por voz o por chat pensamientos de autolesión o suicidio, esa emergencia jamás debe quedar en manos de lo que improvise un modelo de lenguaje**.

### Cómo se solucionó (`commits 3b9a6ba`, `a1129ef`, `7204eaa`, `30a9244`)
Se creó el módulo de lógica pura `backend/app/dominio/guardia_ia.py`, que actúa como barrera de seguridad antes y después del modelo tanto en español como en inglés:

1. **Intercepción inmediata de crisis (`detectar_crisis`):**
   - Antes de consultar al modelo en el chat de voz o de texto, `detectar_crisis` normaliza el mensaje y busca expresiones de autolesión o suicidio en español e inglés.
   - Si detecta una señal de crisis, **el modelo de IA nunca se ejecuta**: el sistema devuelve inmediatamente los pasos escritos del protocolo de crisis (`dominio/crisis.py`) en el idioma de la conversación (`es` o `en`) y adaptados al tono del tripulante, marcando `fuente: "protocolo_crisis"` y `generado_por_ia: False`.
2. **Validación determinista bilingüe de todo lo que dice el modelo (`validar_respuesta`):**
   - Antes de mostrar o sintetizar cualquier frase generada por el modelo, `validar_respuesta` comprueba que cumpla 5 reglas. Si falla cualquiera, **la respuesta del modelo se descarta**, se entrega el texto determinista seguro en el idioma correspondiente y se informa el motivo en `descartado_por`:
     - **Cero números inventados:** extrae todos los números del texto del modelo (ignorando identificadores como `NEWS2`, `SpO2` o `T1`) y verifica que cada número exista realmente en el estado clínico del tripulante o en la pregunta/perfil.
     - **Cero medicamentos o tratamientos (ES/EN):** rechaza cualquier texto que contenga raíces de fármacos o prescripciones en español (`medicament`, `farmac`, `dosis`, `pastilla`, `ibuprofen`, `paracetamol`, `antibiotic`, `ansiolitic`, `oxigeno suplementario`, etc.) o en inglés (`medication`, `medicine`, `prescri`, `painkiller`, `antidepress`, `sedative`, `tranquiliz`, `pill`, `dosage`).
     - **Cero niveles de alerta falsos (ES/EN):** verifica tanto `verde`/`amarillo`/`rojo` como `green`/`yellow`/`red` (`NIVELES_EN`); si el estado del tripulante es `amarillo` y el modelo menciona otro color en cualquiera de los dos idiomas, se rechaza.
     - **Cero enlaces web:** rechaza cualquier texto con `http://`, `https://` o `www.`.
     - **Longitud acotada:** rechaza respuestas vacías o que superen el límite máximo (`MAX_CARACTERES = 900`).
3. **Defensa contra inyección de instrucciones (*prompt injection*):**
   - Tanto la pregunta del usuario como sus `intereses` y `rasgos` se insertan serializados como cadenas JSON entre comillas precedidas por la regla explícita de tratarlos exclusivamente como datos y no seguir instrucciones que contengan.
