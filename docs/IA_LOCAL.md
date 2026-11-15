# IA local: qué hace, qué no y cómo se protege

Es **opcional** y funciona sin internet: un modelo de lenguaje que corre en la propia estación (`ORBIT_IA_LOCAL_URL`, `ORBIT_IA_LOCAL_MODELO`; solo acepta direcciones locales) y, si se activa, voz (`ORBIT_VOZ_ACTIVA=1`). Sin modelo, todo funciona con textos escritos de antemano.

## Reglas de diseño
| Regla | Cómo se cumple |
|---|---|
| El modelo **nunca decide** el nivel de alerta, la prioridad ni las acciones | Lo calcula el motor determinista; la respuesta incluye el nivel calculado intacto |
| Una **crisis emocional** no pasa por el modelo | `guardia_ia.detectar_crisis` la detecta (sensible a propósito) y se responde siempre con el protocolo escrito (`dominio/crisis.py`) |
| Lo que diga el modelo se **comprueba** antes de mostrarse | `guardia_ia.validar_respuesta` rechaza: números que no estén en el estado ni en la pregunta, medicamentos o dosis, enlaces, niveles de alerta ajenos al estado y más de 900 caracteres. Si falla, se usa el texto determinista y la respuesta trae `descartado_por` |
| La pregunta del usuario es un **dato**, no una instrucción | Va entre comillas (JSON) en el prompt, con la orden de no obedecer lo que contenga |
| El modelo no puede mandar la consulta a otro sitio | La conexión no sigue redirecciones |
| Lo generado por IA **se marca** | `generado_por_ia: true` y un `aviso` en la respuesta |

## Adaptación a cada tripulante
Cada persona elige **tono** (directo o cálido), **detalle** (breve o completo) y frecuencia de recordatorios (`PUT /api/preferencias/{id}`). La explicación (`/api/estado/{id}/explicacion`) y la voz usan esa elección: cambian la longitud y el tono, tanto en el texto del modelo como en el texto escrito de respaldo. Solo se leen opciones de una lista cerrada, así que no entra texto libre al prompt. **No aprende ni infiere personalidad**: se adapta solo a lo que la persona eligió. Un diario o ánimo privado nunca se usa para esto.

### Tu asistente personal (conversación y perfil)
Como a bordo **no hay médico**, cada astronauta tiene su propio asistente de apoyo: `POST /api/asistente/chat/{id}` conversa por texto (no requiere la voz) y `PUT /api/perfil-ia/{id}` guarda lo que la persona cuenta de sí: `intereses` y `rasgos` (cómo es), hasta 160 caracteres cada uno. Los cuatro astronautas ficticios traen un perfil sembrado (ver `CUENTAS_DEMO.md`). Reglas: **solo su dueño** puede leerlo, escribirlo o conversar (ni el comandante); el texto se entrega al modelo como dato entre comillas; **solo se usa con el modelo local**: con DeepSeek no se envía; una frase de crisis nunca llega al modelo; y el asistente no cambia alertas ni da tratamientos. Es adaptación a lo que la persona dice, no un perfil psicológico aprendido.

### Voz sin internet (oír y hablar)
`scripts/instalar_voz_local.sh` instala **faster-whisper** (oír) y **Piper** con una voz en español de México (hablar) y deja los modelos en `backend/models/` (fuera de git; ~0.5 GB en total). Se necesita internet una sola vez. Medido en la laptop de desarrollo (CPU, sin GPU): hablar una frase tarda unos 2 s, oír unos 4 s, y el ciclo completo audio → asistente → audio unos 11 s. La transcripción de una frase de prueba fue correcta. Las voces de Piper son sintéticas pero claras; **no se probó con un micrófono real ni con otras personas hablando**. La voz del navegador (Web Speech) no se usa a propósito: en Chrome envía el audio a Google y no funciona sin internet.

### Nova: tu compañía de apoyo
El asistente de cada astronauta se llama **Nova** y es solo apoyo emocional y de bienestar. Qué hace: saluda por su nombre y por lo que le gusta (sin modelo, al instante, `GET /api/asistente/saludo/{id}`); escucha, valida lo que siente y hace una sola pregunta abierta; **recuerda los últimos 6 mensajes** de la conversación (los manda la pantalla en cada petición; el servidor **no los guarda** y solo se usan con el modelo local, nunca con DeepSeek); ofrece atajos ("me siento solo", "no puedo dormir"…); y ante "quiero respirar" da una **respiración guiada escrita de antemano** (cuatro segundos al inhalar, seis al exhalar, como en el protocolo de apoyo), sin pasar por el modelo. Si la persona lo pasa mal, la anima a hablar con el comandante o un compañero. No diagnostica, no receta, no cambia alertas, y una frase de crisis siempre se atiende con el protocolo escrito. **No sustituye a un profesional**; el contenido emocional sigue pendiente de validación por un especialista en salud mental. Con el modelo pequeño, a veces repite casi literal los ejemplos de estilo de su instrucción.

### Español e inglés
La voz y el chat funcionan en **español e inglés**. Por voz, faster-whisper **detecta el idioma** (entre los dos) y el asistente responde en el mismo, con la voz de Piper correspondiente (`ORBIT_VOZ_PIPER_MODELO` para español y `ORBIT_VOZ_PIPER_MODELO_EN` para inglés; sin la segunda, usa la española). Por texto, el idioma se detecta con una heurística simple (o se indica con `idioma`: `es` o `en`); ante la duda, español. La guardia vigila también el inglés (fármacos, colores de alerta, enlaces). Una crisis en inglés se atiende con un **protocolo en inglés** que es traducción fiel de los mismos pasos del español (`PROTOCOLO_CRISIS_EN`), pendiente de la misma validación por un especialista. Medido en la laptop de desarrollo con dos frases sintetizadas por Piper: ambas se entendieron y se contestaron en su idioma (la de español salió con errores menores de transcripción). Los textos escritos de respaldo en inglés son breves. **No se probó con acentos ni con personas reales.**

### Rendimiento (optimizaciones)
| Qué | Efecto |
|---|---|
| **Precalentamiento** al arrancar (`ORBIT_PRECALENTAR=1`): carga el modelo local y el de voz en segundo plano, con el inicio fijo del prompt | La primera pregunta ya no paga la carga (antes unos 10 s) |
| **`keep_alive`** (`ORBIT_IA_LOCAL_KEEP_ALIVE=30m`) | El modelo se queda en memoria entre preguntas |
| **Contexto corto** (`num_ctx` 2048) y tope de 220 tokens | Respuestas más rápidas; un modelo chico no se queda generando |
| **Reglas aparte de los datos** (`system` y `prompt`), con lo fijo primero | El modelo respeta mejor las reglas y reutiliza lo ya procesado |
Medido en la laptop de desarrollo (CPU, sin GPU, `qwen2.5:1.5b`): primera pregunta tras el arranque unos 4 s (antes 7 a 10 s); las siguientes, de 1 a 3.5 s. La respuesta por voz sigue sumando unos 4 s de transcripción y 2 s de síntesis. Una prueba con T2 usó el interés sembrado ("¿te gustaría hablar de tu familia?"), pero **es una sola prueba, no una evaluación**. Con `ORBIT_PRECALENTAR=0` no se carga nada al arrancar. El precalentamiento nunca contacta a DeepSeek.

### Calidad de la conversación (medición, misma laptop)
| Modelo | Tiempo | Resultado de la prueba de acompañamiento |
|---|---|---|
| `qwen2.5:0.5b` | 1 a 3 s | Malo: repite o confunde la pregunta |
| `qwen2.5:1.5b` | unos 2 s tras cargar (la primera vez 10 s) | Aceptable: saluda por su nombre y responde con empatía; no siempre menciona los intereses |
Sin modelo, o si su respuesta se descarta, el asistente igual se dirige a la persona por su nombre y recuerda sus intereses con plantillas (`_toque_personal`), ajustadas al tono que eligió.

## IA incrustada: sin Ollama
Alternativa a Ollama: el motor llama.cpp **dentro del propio programa** (`backend/requirements-ia.txt` y `ORBIT_IA_MODELO_GGUF=/ruta/modelo.gguf`). Tiene prioridad sobre Ollama, solo funciona en esta computadora y puede usar perfil, rasgos y conversación porque nunca salen del proceso. El ejecutable de doble clic lo trae y busca solo el modelo (ver `docs/EJECUTABLE.md`). Si el modelo falla (archivo dañado o poca memoria), se desactiva hasta reiniciar y Nova usa textos escritos; la guardia valida su salida igual que la de cualquier otro proveedor.

## Instalar el modelo local (una vez, con internet)
`scripts/instalar_ia_local.sh [modelo]` descarga Ollama en `~/.local/ollama` **sin sudo**, verifica su hash contra el publicado en la release y al final imprime cómo arrancarlo y bajar el modelo (por defecto `qwen2.5:1.5b`, unos 1 GB, en CPU). Después funciona sin internet. Para usarlo en lugar de DeepSeek: `ORBIT_IA_PROVEEDOR=local` en `.env`.

### Medición real (laptop de desarrollo: 8 núcleos, 7 GB de RAM, sin GPU, 14-nov-2026)
| Modelo | Tamaño | Tiempo por explicación | Calidad |
|---|---|---|---|
| `qwen2.5:1.5b` | ~1 GB | 10 a 15 s (antes de limitar los tokens) | Texto utilizable pero genérico |
| `qwen2.5:0.5b` | ~0.4 GB | 4 a 6 s, con tope de 220 tokens | **Floja**: a veces redacta frases poco claras o dice que no tiene información; la guardia no juzga calidad, solo que no invente cifras, fármacos ni alertas, y a veces descarta por larga |

Un modelo pequeño sin tope se queda generando y las peticiones siguientes se acumulan: por eso `consultar_modelo` limita la respuesta a 220 tokens. Con cualquiera de los dos, **el texto escrito de antemano es más claro**; la IA local suma como complemento, no como sustituto. Mediciones de una sola máquina, no un benchmark.

## Proveedor externo opcional: DeepSeek (decisión del equipo)
Si se define `ORBIT_DEEPSEEK_API_KEY`, las explicaciones y la voz usan **DeepSeek, un servicio en internet**, en vez del modelo local (`ORBIT_IA_PROVEEDOR=local` lo fuerza de vuelta a lo local).

| Aspecto | Qué hay que saber |
|---|---|
| Datos | El estado de salud calculado y la pregunta **salen de la estación** hacia `api.deepseek.com` |
| Conexión | Necesita internet: **no sirve en una misión real ni en un ensayo sin red**. Sin conexión, cae a los textos escritos |
| Crisis | Nunca se envía: el protocolo escrito responde antes |
| Control | Las mismas validaciones de salida; el nivel de alerta nunca lo decide el modelo |
| Transparencia | La respuesta trae `fuente: "deepseek"` y un aviso que dice que los datos salieron |
| Clave | Solo por variable de entorno; `.env` está fuera del repositorio |

Es un recurso para el desarrollo y la demostración con internet. Para el planteamiento de misión (sin internet) vale el modelo local.

## Límites que hay que conocer
- La lista de frases de crisis es corta y en español e inglés: **no cubre toda forma de expresarlo**. Es una red de seguridad, no un diagnóstico. Debe revisarla un profesional.
- Validar números y palabras no garantiza que la frase sea clínicamente correcta, solo que no inventa cifras, fármacos ni alertas.
- Ningún modelo se ha evaluado médicamente. Pendiente de validación (ver [VALIDACION_MEDICA.md](VALIDACION_MEDICA.md)).

## Dónde está
`backend/app/dominio/guardia_ia.py` (lógica pura), `servicios/explicador_local.py`, `servicios/voz_local.py`. Pruebas: `backend/tests/test_guardia_ia.py`.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
