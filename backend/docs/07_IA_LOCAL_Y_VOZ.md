# 07 — IA Local Explicativa, Voz Offline, Asistente "Nova" y Guardia de IA

Este módulo incorpora capacidades opcionales de **Inteligencia Artificial local**, la compañía de apoyo **Nova** por **texto y voz (`push-to-talk`) en español e inglés** y un **perfil privado de intereses y rasgos**, pensadas para asistir a la tripulación cuando tiene las manos ocupadas o necesita acompañamiento en misiones largas, **sin romper nunca el principio de que las decisiones médicas las toman reglas deterministas**.

Para detalles adicionales de política, límites y defensas del prompt puedes consultar también [IA_LOCAL.md](../../docs/IA_LOCAL.md) y [AUDITORIA_SEGURIDAD.md](../../docs/AUDITORIA_SEGURIDAD.md).

---

## 1. Explicador con IA Local, Estilo y Optimizaciones en CPU (`GET /api/estado/{tid}/explicacion`)

### Qué problema había
Un tripulante puede querer una explicación redactada en lenguaje natural sobre por qué su estado general está en verde, amarillo o rojo y qué señales influyeron. Sin embargo, usar un modelo de inteligencia artificial en medicina espacial tiene cuatro riesgos graves:
1. Que el modelo "alucine" un diagnóstico, invente valores o cambie el nivel de una emergencia.
2. Que ignore el estilo preferido del astronauta (por ejemplo, dar un texto largo cuando pidió respuestas breves y directas durante una maniobra).
3. Que un modelo pequeño en la computadora de la nave consuma demasiado procesador o tarde 10 segundos en cargar en la primera pregunta.
4. Que el servidor de IA no esté encendido o tarde demasiado y deje al tripulante sin respuesta.

### Cómo se solucionó (`commits 252366a`, `a1129ef`, `b7c887a`, `b7f8d68`, `74bd93c`)
En `backend/app/api/asistente.py` y `backend/app/servicios/explicador_local.py`:
- **La IA solo explica, nunca decide:** primero el motor clínico determinista calcula el estado (`servicio_estado.estado_tripulante`). El modelo recibe únicamente ese resultado ya calculado con instrucciones estrictas de resumirlo en español sin diagnosticar, sin recetar medicamentos y recordando que las acciones procedimentales tienen prioridad. El campo `nivel_general` que devuelve la ruta es siempre el del motor clínico intacto.
- **Adaptación automática a `tono` y `detalle` (`commit b7c887a`):** la ruta lee las preferencias guardadas del tripulante (`tono`: `directo` o `calido`; `detalle`: `breve` o `completo`) y ajusta tanto las instrucciones al modelo (45 palabras en modo breve vs 95 en completo) como el respaldo determinista (`_fallback`).
- **Optimizaciones de velocidad y memoria en CPU (`commits b7f8d68`, `74bd93c`):**
  - **Precalentamiento al arrancar (`ORBIT_PRECALENTAR=1`):** carga en segundo plano el modelo local y el modelo de voz con la parte fija del *prompt* (`SISTEMA_BASE`), reduciendo la espera de la primera pregunta de ~10 s a ~4 s (y nunca contacta a DeepSeek).
  - **Modelo residente en memoria (`ORBIT_IA_LOCAL_KEEP_ALIVE=30m`):** evita recargar el modelo entre preguntas.
  - **Contexto corto (`num_ctx=2048`), separación de `system` vs `prompt` y tope de `220` tokens:** permite que modelos locales ligeros (`qwen2.5:1.5b` o `0.5b`) reutilicen lo ya procesado y respondan rápido en CPU.
- **Candado contra redirecciones (`_url_local` y `_SinRedireccion`):** verifica que `ORBIT_IA_LOCAL_URL` apunte exclusivamente a `localhost`, `127.0.0.1` o `::1` y **prohíbe seguir redirecciones HTTP (`301`/`302`/`307`)**.
- **Respaldo instantáneo por reglas (`_fallback`):** si no se configuró un modelo, o si tarda más de `ORBIT_IA_LOCAL_TIMEOUT_S`, falla o su texto es rechazado por la Guardia de IA, el sistema responde automáticamente con la explicación determinista (`fuente: "reglas_locales"`, `generado_por_ia: False`).

---

## 2. "Nova": Compañía de Apoyo, Perfil Privado (`intereses` y `rasgos`), Saludo, Memoria Corta y Respiración Guiada (`perfil_ia.py`)

### Qué problema había
En una misión de meses o años lejos de la Tierra y sin médico a bordo, el aislamiento pesa. Los astronautas necesitaban una compañía de apoyo cercana (llamada **Nova**) que pudiera saludarlos por su nombre, recordar qué los motiva en Tierra (`intereses`) y cómo son en sus propias palabras (`rasgos`), ofrecerles ejercicios de respiración cuando sienten ansiedad y mantener el hilo de la conversación reciente, **sin guardar un historial psicológico en el servidor, sin que el comandante pueda leerlo y sin enviarlo jamás a internet**.

### Cómo se solucionó (`commits 3730ff7`, `851e767`, `d824017`, `16f3b2a`, `d8b8f07`)
Se crearon `backend/app/api/perfil_ia.py`, `backend/app/servicios/perfil_ia.py`, `backend/app/repositorios/perfil_ia.py` y la tabla `perfil_ia` en `schema.sql`:
1. **Perfil privado de intereses y rasgos (`GET /api/perfil-ia/{tid}` y `PUT /api/perfil-ia/{tid}`):**
   - Permite a cada tripulante guardar hasta 160 caracteres para sus `intereses` y hasta 160 caracteres para sus `rasgos`, pudiendo actualizarlos juntos o por separado.
   - Los 4 astronautas ficticios (`Valeria Montoya`, `Mateo Ríos`, `Camila Ortega` y `Andrés Leal`) traen perfiles sembrados de demostración en `semilla.py`.
   - **Privacidad absoluta (`exigir_propietario`):** solo el propio dueño (`actor.id == tid`) puede leerlo o modificarlo (`403` para cualquier otro usuario, incluido el comandante).
2. **Saludo instantáneo y atajos de conversación (`GET /api/asistente/saludo/{tid}`, `commit d8b8f07`):**
   - Sin tocar al modelo, **Nova** saluda al instante al astronauta por su nombre de pila, menciona su primer interés guardado y le sugiere 4 atajos de conversación en español o inglés (`"Me siento solo"`, `"Estoy estresado"`, `"No puedo dormir"`, `"Quiero respirar"` / `"I feel lonely"`, `"I'm stressed"`, `"I can't sleep"`, `"I want to breathe"`).
3. **Respiración guiada determinista (`_guia_respiracion`, `fuente: "guia_respiracion"`, `commit d8b8f07`):**
   - Cuando el astronauta pide respirar, **Nova no pasa por el modelo de IA**: entrega directamente un ejercicio de respiración guiada escrito y revisado de antemano (**inhalar 4 segundos, sostener y exhalar 6 segundos**) en su idioma (`es` o `en`).
4. **Chat escrito bilingüe con memoria corta de 6 mensajes sin persistencia (`POST /api/asistente/chat/{tid}`, `commit d8b8f07`):**
   - Permite conversar por texto con **Nova** en español o inglés. La pantalla envía los últimos 6 mensajes (`historial`) en cada petición; **el servidor jamás los guarda en SQLite** y **solo los pasa al modelo local**.

---

## 3. Conversación por Voz Bilingüe (`POST /api/voz/chat/{tid}`) e Instaladores Offline

### Cómo se solucionó (`commits 252366a`, `5edee80`, `a1129ef`, `300bcfc`, `1a71dbf`, `851e767`, `38f86f4`, `30a9244`, `b4e187f`)
En `backend/app/api/voz.py`, `backend/app/servicios/voz_local.py` y `scripts/`:
1. **Privacidad por dueño (`commit 851e767`):** `POST /api/voz/chat/{tid}` verifica que quien habla sea el propio tripulante (`actor.id == tid`).
2. **Flujo de voz en 3 pasos 100 % local, bilingüe (`es`/`en`) y sin rastro en base de datos:**
   - **Escuchar y detectar/normalizar idioma (`transcribir_con_idioma` y `normalizar_idioma`):** transcribe localmente con `faster-whisper` (`compute_type="int8"`), aceptando la preferencia de idioma de la interfaz (`es`, `en`, `es-MX`, `en-US` o `auto`) o detectándolo automáticamente. El archivo temporal se borra inmediatamente y **jamás se guarda en SQLite**.
   - **Validación limpia de audio corrupto (`commit 38f86f4`):** devuelve un `422` claro si el audio está truncado o en formato incompatible.
   - **Pensar y Hablar en el mismo idioma (`sintetizar`):** sintetiza el audio WAV (`base64`) usando `piper` con la voz española (`ORBIT_VOZ_PIPER_MODELO`) o la voz inglesa (`ORBIT_VOZ_PIPER_MODELO_EN`).
3. **Scripts de aprovisionamiento previo al vuelo (`scripts/instalar_ia_local.sh` y `scripts/instalar_voz_local.sh`):** instalan Ollama sin `sudo` (verificando su hash SHA-256) y descargan en `backend/models/` `faster-whisper` y las voces de `piper` en español e inglés.

---

## 4. Modo Automático (Failover Local → DeepSeek) sin Exponer Datos Personales

### Qué problema había
En demostraciones con internet, si Ollama local no está corriendo y el sistema usa DeepSeek como respaldo (`ORBIT_IA_PROVEEDOR=automatico` o `deepseek`), había que asegurar que **jamás saliera hacia la nube ningún dato personal o íntimo del astronauta** (ni su nombre, ni sus intereses, ni sus rasgos, ni su conversación reciente).

### Cómo se solucionó (`commits 507c8aa`, `f59636e`, `6bbf301`, `ec96ddd`, `b86f3a7`, `5642f98`)
En `backend/app/servicios/explicador_local.py` y `backend/app/servicios/voz_local.py`:
- **Failover inteligente (`commit ec96ddd`):** en modo `automatico`, intenta primero el modelo local (`Ollama`); solo si el modelo local no está disponible y existe `ORBIT_DEEPSEEK_API_KEY`, recurre a DeepSeek antes de caer al respaldo determinista por reglas. Con `ORBIT_IA_PROVEEDOR=local`, jamás contacta a internet.
- **Dos versiones del prompt y cero datos personales hacia DeepSeek (`commit b86f3a7`):**
  - Cuando se consulta a DeepSeek (ya sea de forma directa o como respaldo), se construye una versión recortada del *prompt* (`prompt_nube` / `sistema_nube`) que **jamás incluye el `nombre` del astronauta, ni sus `intereses`, ni sus `rasgos`, ni el `historial` de conversación**.
  - Además, cada vez que una consulta sale hacia DeepSeek, se anota el evento `ia_salida_nube` en la bitácora de auditoría (sin el texto) y la respuesta incluye `fuente: "deepseek"` con el `aviso` explícito de que datos del estado salieron de la estación.

---

## 5. Guardia de IA Bilingüe, Saneado de Prompt, Antifiltración y Límites de Uso (`guardia_ia.py` y `limites.py`)

### Qué problema había
Un usuario o un texto malformado podría intentar manipular al modelo con instrucciones ocultas (*prompt injection*, caracteres invisibles o etiquetas de sistema como `<|im_start|>` o `system:`), pedirle que revele sus instrucciones internas, o lanzar decenas de peticiones seguidas para saturar el procesador de la nave.

### Cómo se solucionó (`commits 3b9a6ba`, `a1129ef`, `7204eaa`, `30a9244`, `99e59da`, `5642f98`)
En `backend/app/dominio/guardia_ia.py` y `backend/app/servicios/limites.py`:

1. **Intercepción inmediata de crisis (`detectar_crisis`):**
   - Antes de aplicar límites de uso o tocar el modelo, busca expresiones de autolesión o suicidio en español e inglés. Si detecta una señal de crisis, **el modelo nunca se ejecuta y los límites de tasa nunca la bloquean**: responde siempre con el protocolo de crisis escrito (`dominio/crisis.py`).
2. **Saneado de entrada contra inyección (`sanear_para_prompt` y `parece_inyeccion`, `commit 99e59da`):**
   - Todo texto del usuario (pregunta, historial, nombre, intereses, rasgos) pasa por normalización Unicode (`NFKC`), eliminando caracteres invisibles/de control, marcas de plantilla de chat (`<|...|>`, `[INST]`, `<<SYS>>`), encabezados que imitan un rol (`system:`, `assistant:`) y bloques de código.
   - Si `parece_inyeccion` detecta un intento evidente de cambiar las reglas o extraer el *prompt*, anota `intento_inyeccion` en la auditoría **sin guardar el texto ni identificar a la persona**.
3. **Validación determinista y antifiltración de la salida (`validar_respuesta` y `_filtra_instrucciones`):**
   - Antes de mostrar o hablar cualquier respuesta del modelo, comprueba 6 reglas estrictas (si falla cualquiera, se descarta y se entrega el respaldo determinista con `descartado_por`):
     - **Antifiltración de instrucciones internas (`_filtra_instrucciones`):** si la respuesta copia 6 palabras seguidas del *prompt* interno del sistema (`secretos`), se descarta.
     - **Cero números inventados:** todo número debe existir en el estado clínico o en la pregunta.
     - **Cero medicamentos o tratamientos (ES/EN):** bloquea raíces de fármacos en español e inglés.
     - **Cero niveles de alerta falsos (ES/EN):** bloquea menciones a colores del semáforo (`verde`/`amarillo`/`rojo` o `green`/`yellow`/`red`) que no correspondan al estado actual.
     - **Cero enlaces web (`http://`, `https://`, `www.`)** y **longitud máxima acotada (`900` caracteres)**.
4. **Límites de uso por persona y concurrencia (`backend/app/servicios/limites.py`, `commit 99e59da`):**
   - Limita el uso del modelo a **30 peticiones por minuto por persona** (`ORBIT_IA_PETICIONES_POR_MIN`) y un máximo de **2 inferencias simultáneas** (`ORBIT_IA_MAX_SIMULTANEAS`). Si se supera el tope, responde inmediatamente `429` con cabecera `Retry-After` y registra `limite_ia` en la auditoría.

---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Antigravity (Google DeepMind)** sobre base técnica documentada con **Claude (Anthropic / Claude Code)**.
> - **Justificación de uso:** Se utilizó para estructurar y explicar en lenguaje claro y sin tecnicismos la arquitectura y los módulos del backend a partir del código fuente y el historial de commits, bajo la definición conceptual y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
