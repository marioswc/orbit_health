# 07 — IA Local Explicativa y Asistente de Voz Offline

Este módulo incorpora capacidades opcionales de **Inteligencia Artificial local** y **conversación por voz (`push-to-talk`)** pensadas para asistir a la tripulación cuando tiene las manos ocupadas o quiere un resumen hablado de su estado, **sin romper nunca el principio de que las decisiones médicas las toman reglas deterministas y sin depender de internet**.

---

## 1. Explicador con IA Local (`GET /api/estado/{tid}/explicacion`)

### Qué problema había
Un tripulante puede querer una explicación redactada en lenguaje natural sobre por qué su estado general está en verde, amarillo o rojo y qué señales influyeron. Sin embargo, usar un modelo de inteligencia artificial en medicina espacial tiene tres riesgos graves:
1. Que el modelo "alucine" un diagnóstico, invente valores o cambie el nivel de una emergencia.
2. Que intente conectarse a un servidor externo en internet (imposible en el espacio profundo y riesgoso para la privacidad).
3. Que el servidor de IA no esté encendido o tarde demasiado y deje al tripulante sin respuesta.

### Cómo se solucionó (`commit 252366a`)
En `backend/app/api/asistente.py` y `backend/app/servicios/explicador_local.py`:
- **La IA solo explica, nunca decide:** primero el motor clínico determinista calcula el estado (`servicio_estado.estado_tripulante`). El modelo local (`ORBIT_IA_LOCAL_MODELO`, por ejemplo `qwen2.5:3b` vía Ollama) recibe únicamente ese resultado ya calculado con instrucciones estrictas de resumirlo en español (máximo 120 palabras) sin diagnosticar, sin recetar medicamentos y recordando que las acciones procedimentales tienen prioridad. El campo `nivel_general` que devuelve la ruta es siempre el del motor clínico intacto.
- **Candado contra internet (`_url_local`):** el código verifica que la dirección configurada en `ORBIT_IA_LOCAL_URL` apunte exclusivamente a la propia computadora (`localhost`, `127.0.0.1` o `::1`). Si alguien configura por error una dirección externa en internet, el sistema se niega a consultarla.
- **Respaldo instantáneo por reglas (`_fallback`):** si no se configuró un modelo local, o si el modelo tarda más de `ORBIT_IA_LOCAL_TIMEOUT_S` (4 segundos por defecto) o falla, el sistema responde automáticamente con una explicación clara armada por reglas locales (`fuente: "reglas_locales"`). Así la función siempre responde.

---

## 2. Conversación por Voz Local (`POST /api/voz/chat/{tid}`)

### Qué problema había
Durante un procedimiento a bordo, un astronauta puede necesitar preguntar en voz alta por su estado sin usar el teclado. Para lograrlo sin red y en una computadora de estación espacial, había que resolver:
1. Cómo transcribir la voz, generar la respuesta y hablarla de vuelta **sin internet y sin guardar grabaciones privadas en la base de datos**.
2. Cómo evitar que la librería de voz intente conectarse a internet para descargar modelos por su cuenta.
3. Cómo evitar que un audio enorme o varias peticiones de voz al mismo tiempo saturen el procesador (CPU) y la memoria de la nave.

### Cómo se solucionó (`commits 252366a`, `5edee80`)
En `backend/app/api/voz.py` y `backend/app/servicios/voz_local.py`:

1. **Flujo de voz en 3 pasos 100 % local y sin rastro en base de datos:**
   - **Escuchar (voz a texto):** recibe audio crudo (`.wav`, `.webm`, `.ogg`, `.mp3`, `.m4a`) y lo transcribe en el procesador local usando `faster-whisper` (`compute_type="int8"`). El archivo temporal se borra inmediatamente en un bloque `finally` y **jamás se guarda en SQLite ni entra a la cola de Tierra**.
   - **Pensar (respuesta acotada):** combina la pregunta transcrita con el estado clínico actual y las preferencias de estilo del tripulante (`tono` y `detalle`), prohibiendo leer o inferir nada de su diario privado o de su ánimo. Si el modelo local no está disponible, responde con la plantilla segura de reglas locales.
   - **Hablar (texto a voz opcional):** si se configuró `ORBIT_VOZ_PIPER_MODELO`, convierte el texto de respuesta en un audio WAV codificado en `base64` usando `piper` localmente.
2. **Bloqueo de descargas externas (`ORBIT_VOZ_STT_LOCAL_ONLY=1`, `commit 5edee80`):**
   - Exige que `ORBIT_VOZ_STT_MODELO` apunte a una carpeta local que ya exista en disco y activa `local_files_only=True` en Whisper, impidiendo cualquier intento de descarga por red.
3. **Protección de tamaño, longitud y CPU (`commit 5edee80`):**
   - **Límite de tamaño de audio (`ORBIT_VOZ_MAX_AUDIO_BYTES`):** valida tanto la cabecera `Content-Length` (`413 Audio demasiado grande`) como los bytes recibidos (máximo 10 MB por defecto) para no agotar la memoria.
   - **Límite de caracteres en la respuesta (`ORBIT_VOZ_MAX_RESPUESTA_CARACTERES`):** recorta la respuesta del modelo a un máximo de **600 caracteres** antes de enviarla al sintetizador de voz, evitando que un texto largo congele la generación de audio.
   - **Un solo turno de voz a la vez (`_TRABAJO_VOZ = BoundedSemaphore(1)`):** como transcribir y sintetizar voz consume bastante procesador, un semáforo permite solo una inferencia de voz activa a la vez. Si llega otra petición simultánea, devuelve de inmediato `429` (*"La capacidad de voz está ocupada; inténtalo de nuevo"*) en lugar de colapsar el servidor a bordo.
