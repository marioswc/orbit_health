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

## Límites que hay que conocer
- La lista de frases de crisis es corta y en español e inglés: **no cubre toda forma de expresarlo**. Es una red de seguridad, no un diagnóstico. Debe revisarla un profesional.
- Validar números y palabras no garantiza que la frase sea clínicamente correcta, solo que no inventa cifras, fármacos ni alertas.
- Ningún modelo se ha evaluado médicamente. Pendiente de validación (ver [VALIDACION_MEDICA.md](VALIDACION_MEDICA.md)).

## Dónde está
`backend/app/dominio/guardia_ia.py` (lógica pura), `servicios/explicador_local.py`, `servicios/voz_local.py`. Pruebas: `backend/tests/test_guardia_ia.py`.
