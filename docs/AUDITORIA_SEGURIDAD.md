# Auditoría de seguridad

```bash
backend/.venv/bin/python scripts/auditoria_seguridad.py            # solo lee; sale con código 1 si hay algún FALLO
backend/.venv/bin/python scripts/auditoria_seguridad.py --arreglar # además restringe los permisos del .env (chmod 600)
```
Hay una prueba automática (`test_auditoria_seguridad.py`) que corre el script sin red. Nunca imprime el valor de una clave.

## Qué revisa
| Área | Comprobación |
|---|---|
| Secretos | Claves y llaves privadas en archivos versionados y en el historial de git; `.env`, `models/`, `.venv` fuera de git; permisos del `.env` |
| Configuración | Autenticación, API de demostración, dirección de escucha, proveedor de IA (si hay clave de DeepSeek y no está forzado el modo local, los datos salen de la estación) |
| Código | SQL armado con texto, `shell=True`, `eval`/`exec`, `pickle`, HTML inyectable en el frontend, texto de usuarios en los registros |
| Aplicación | Cabeceras de seguridad, API sin caché, CORS cerrado, rutas públicas, modelo local solo en loopback |
| Prompt de la IA | Saneado de entradas, instrucción de no revelar el prompt, antifiltración de la salida, crisis antes del modelo, límites de uso |
| Dependencias | `pip-audit` sobre `backend/requirements.txt` (necesita internet y `pip install pip-audit`) |

## Cómo se protege el prompt de la IA
1. **Saneado** (`guardia_ia.sanear_para_prompt`): todo texto del usuario (pregunta, historial, nombre, perfil) pasa por Unicode NFKC y pierde caracteres de control e invisibles, marcas de plantilla de chat (`<|...|>`, `[INST]`), encabezados que imitan un rol (`system:`) y bloques de código.
2. **Dato entre comillas**: lo del usuario va como JSON citado y el sistema declara que no se obedecen instrucciones que contenga.
3. **Instrucciones separadas** de los datos (`system` y `prompt`) y una regla expresa de no revelarlas ni cambiar de papel.
4. **Antifiltración de la salida**: si una respuesta copia seis palabras seguidas de las instrucciones, se descarta (`filtra sus instrucciones internas`).
5. **Validación de la salida**: sin cifras inventadas, fármacos, enlaces ni colores de alerta ajenos.
6. **La crisis y la respiración guiada** son texto escrito de antemano y no pasan por el modelo; la crisis nunca se frena por los límites.
7. **Límites**: 30 peticiones por minuto por persona y 2 simultáneas con el modelo (`ORBIT_IA_PETICIONES_POR_MIN`, `ORBIT_IA_MAX_SIMULTANEAS`); sobre el tope, responde 429 con `Retry-After`.
8. Los intentos evidentes de inyección se **registran sin guardar el texto**.

9. **Respaldo a la nube sin datos personales**: si el proveedor es automático (primero el modelo local y, si falla, DeepSeek) o es la nube directa, a DeepSeek solo viajan las preferencias de trato, el estado calculado y la pregunta. **Nunca** el perfil, los rasgos, la conversación reciente ni el nombre (`explicador_local.datos_personales_permitidos` y el parámetro `externo` de `consultar_modelo`). Lo cubren dos pruebas. Lo que la persona escribe en la pregunta sí viaja, y la respuesta lo avisa (`aviso`).

## Registro de auditoría (qué se anota)
La bitácora (`GET /api/auditoria`, solo el comandante; `/api/auditoria/verificar` comprueba su cadena de hashes) anota **quién hizo qué y cuándo, nunca el contenido**.

| Acción | Cuándo |
|---|---|
| `inscripcion`, `login`, `logout`, `bloqueo_temporal`, `recuperacion`, `reinicio_pin` | Acceso y credenciales |
| `enlace_cambio` | Alguien cambia el estado o el entorno del enlace |
| `lectura_a_tercero` | Un compañero registra signos de otro |
| `consentimiento_salud_mental`, `atencion_salud_mental`, `revocacion_salud_mental` | Avisos que la propia persona decidió compartir |
| `simulacion_iniciada`, `simulacion_detenida` | Alguien enciende o apaga la misión simulada (escribe datos de demo) |
| `ia_salida_nube` | **Una consulta salió de la estación hacia DeepSeek** (con la ruta y si fue directa o respaldo), sin el texto |
| `limite_ia` | Alguien superó el tope de peticiones al asistente |
| `intento_inyeccion` | Se detectó un intento evidente de cambiar las reglas del asistente; **sin texto y sin identificar a la persona** (la heurística puede equivocarse) |

**Lo que a propósito NO se anota:** una crisis, la respiración guiada, lo que alguien escribe a Nova, su perfil, el diario, el ánimo ni el PHQ-2. El comandante lee esta bitácora, y el contenido emocional es solo de su dueño.

## Cabeceras HTTP
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy` (solo micrófono), `Cross-Origin-Opener-Policy`, y `Cache-Control: no-store` en la API.

## Lo que NO cubre (declarado)
- **Sin CSP estricta**: `index.html` lleva un script en línea (tema claro u oscuro). Pendiente: moverlo a un archivo o fijar su hash.
- **Sin TLS ni cifrado de la base**: en una red de cabina, un tercero con acceso a la red podría leer el tráfico. Fuera de alcance de esta entrega.
- Con `ORBIT_AUTH=0` cualquiera con acceso al equipo ve todo: aceptable solo en demo local. Con `ORBIT_DEMO_API=1` hay endpoints de demostración.
- El saneado y la detección de inyección son heurísticos: no garantizan que ningún texto malicioso pase. Por eso la salida también se valida.
- Una auditoría hecha por quien escribió el código no sustituye una revisión independiente.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
