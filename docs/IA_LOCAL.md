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
