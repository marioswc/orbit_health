# 06 — Seguridad a Bordo, Auditoría, Simulación en Vivo y Pruebas de Calidad

Este documento explica cómo se protegió el acceso al sistema para operar dentro de una nave sin internet, cómo se audita la seguridad de forma automática, cómo funcionan las herramientas de demostración en vivo y cómo las pruebas verifican el código, la PWA y la documentación.

Para detalles específicos de la auditoría de seguridad y despliegue puedes consultar también [AUDITORIA_SEGURIDAD.md](../../docs/AUDITORIA_SEGURIDAD.md), [INSTALAR_COMO_APP.md](../../docs/INSTALAR_COMO_APP.md) y [EJECUTABLE.md](../../docs/EJECUTABLE.md).

---

## 1. Seguridad Pensada para Operar a Bordo (`ORBIT_AUTH=1`)

### Qué problema había
No se podía copiar el sistema de usuarios de una página web normal porque:
1. En el espacio profundo **no hay internet ni servidor de correo** para enviar enlaces de "olvidé mi contraseña".
2. Si un tripulante falla su clave varias veces y la cuenta se bloquea para siempre, **podría impedir atender una emergencia médica a bordo**.
3. Si el tripulante T1 queda inconsciente, su compañero T2 necesita poder registrarle sus signos vitales desde su propia sesión.

### Cómo se solucionó (`commits 55c45bb`, `484fbcc`, `ce1e339`, `58ae017`, `60c3513`, `0ec4995`, `7c8d989`, `30a9244`, `16f3b2a`, `99e59da`, `5642f98`)
En `backend/app/dominio/seguridad.py`, `backend/app/servicios/auth.py`, `backend/app/api/auth.py` y `backend/app/main.py`:
- **Dos roles realistas a bordo y un único comandante (`commits 0ec4995`, `30a9244`):** dado que en una tripulación pequeña todos son astronautas y no viaja un médico dedicado a bordo, existen dos roles: `tripulante` (T2, T3, T4) y `comandante` (T1). Además, `auth.inscribir` verifica con `repo.hay_comandante` que **solo pueda existir un comandante en toda la tripulación**.
- **Cuatro astronautas ficticios con identidad y perfil propio (`backend/app/fuentes/semilla.py`, `commit 16f3b2a`):** la semilla inicializa 4 tripulantes simulados con nombre, profesión, rasgos, intereses y trato preferido:
  - **T1 — Valeria Montoya** (Comandante, PIN `111111`, trato `directo` / `completo`)
  - **T2 — Mateo Ríos** (Especialista de misión, PIN `222222`, trato `calido` / `completo`)
  - **T3 — Camila Ortega** (Ingeniero, PIN `333333`, trato `directo` / `breve`)
  - **T4 — Andrés Leal** (Piloto, PIN `444444`, trato `calido` / `breve`)
  Documentado también en [CUENTAS_DEMO.md](../../docs/CUENTAS_DEMO.md).
- **PIN numérico de 6 a 10 dígitos (`POST /api/auth/login`):** cómodo para pantallas táctiles o uso con guantes (`PBKDF2-HMAC-SHA256` con sal única).
- **Bloqueos temporales, nunca permanentes:** tras 5 intentos fallidos, la cuenta se bloquea solo por **5 minutos** (`423 Locked`).
- **Recuperación 100 % sin internet:** mediante **código de recuperación de un solo uso** en `POST /api/auth/recuperar` o reinicio por el **comandante** en `POST /api/auth/reiniciar-pin/{tid}`.
- **Permisos adaptados a emergencias y privacidad:**
  - **Datos clínicos (`POST /api/lecturas`, `GET /api/estado/{tid}`):** cualquier tripulante autenticado puede ver y registrar signos vitales de un compañero incapacitado, quedando grabado en la **auditoría** (`lectura_a_tercero`).
  - **Datos privados (`diario`, `animo`, `tamizajes`, `preferencias`, `perfil-ia`, `asistente/chat`, `asistente/saludo`, `voz/chat`):** exclusivos de su dueño, sin excepción de rol (ni el comandante puede verlos).
  - **Operaciones de mando (`/api/enlace`, `/api/auditoria`, atender avisos consentidos y correr demos):** reservadas al **comandante**.
- **Auditoría con cadena de hash sin exponer contenido (`GET /api/auditoria` y `GET /api/auditoria/verificar`, `commit 5642f98`):**
  - Registra **quién hizo qué y cuándo, pero jamás el contenido**: inicios de sesión, cambios de enlace, lecturas a terceros, avisos consentidos, encendido/apagado de la simulación (`simulacion_iniciada`, `simulacion_detenida`), salida de una consulta hacia DeepSeek (`ia_salida_nube`), exceso de peticiones (`limite_ia`) o sospecha de inyección de prompt (`intento_inyeccion`, sin texto ni autor).
  - **Lo que jamás se anota:** crisis emocionales, ejercicios de respiración, lo que alguien platica con Nova, su perfil, diario, ánimo o PHQ-2.
- **Cabeceras HTTP de seguridad (`backend/app/main.py`, `commit 99e59da`):** todas las respuestas incluyen `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy` (solo micrófono), `Cross-Origin-Opener-Policy: same-origin` y `Cache-Control: no-store` en `/api`.

---

## 2. Script de Auditoría de Seguridad, Asistente de Inicio, PWA y Docker

### Qué problema había
Antes de presentar o desplegar el sistema en una máquina nueva, era necesario verificar de un vistazo que no hubiera claves expuestas, permisos inseguros o configuraciones riesgosas, además de facilitar la instalación en un paso.

### Cómo se solucionó (`commits fb4a5cf`, `df412b6`, `0770da3`, `067cb9f`)
1. **Auditoría automática de seguridad (`scripts/auditoria_seguridad.py` y `test_auditoria_seguridad.py`):**
   - Verifica secretos en archivos y en el historial de Git, permisos de `.env`, ausencia de SQL inseguro o `eval`/`exec`/`shell=True`, cabeceras HTTP, defensas del *prompt* de IA y advierte si las cuentas demo con PIN público (`111111`..`444444`) siguen activas cuando `ORBIT_AUTH=1`.
2. **Preparación en un paso y asistente interactivo (`scripts/preparar.sh`, `scripts/asistente_inicio.sh` y `scripts/poner_env.py`):**
   - `preparar.sh` crea el entorno virtual del backend, instala dependencias, descarga y carga la calibración de PhysioNet y compila el frontend.
   - `asistente_inicio.sh` guía paso a paso en español o inglés para elegir el modo (demo sin PIN, demo con los 4 astronautas, IA local con Ollama o respaldo con DeepSeek) escribiendo el archivo `.env` con permisos restringidos (`0600`).
3. **App instalable (PWA), Compresión GZip, Ejecutable de Doble Clic y Contenedor Docker (`Dockerfile`, `docker-compose.yml`, `scripts/lanzador.py`, `scripts/crear_ejecutable.sh`, `test_pwa.py`, `test_lanzador.py`):**
   - La interfaz incluye manifiesto, íconos y Service Worker que guarda la carcasa visual para abrir al instante sin conexión, pero **jamás guarda respuestas clínicas de `/api` en caché del navegador** para evitar mostrar signos vitales viejos como si fueran actuales. Además, `main.py` aplica `GZipMiddleware` para comprimir respuestas HTTP grandes.
   - **Ejecutable autónomo de doble clic (`scripts/lanzador.py` y `scripts/crear_ejecutable.sh`, `commits c947548`, `632e679`):** empaqueta servidor, interfaz y datos en un solo archivo (~24 MB) que arranca en ~2 s sin requerir Python ni Node, guarda la base de datos y respaldos en la carpeta del propio usuario (`%LOCALAPPDATA%\ORBIT Health` / `~/.local/share/orbit-health`), detecta instancias ya abiertas y **jamás lee archivos `.env` de carpetas temporales compartidas** (`config._ruta_dotenv`).
   - Incluye `Dockerfile` sin privilegios (`non-root`) que publica únicamente en `127.0.0.1:3000`.

---

## 3. Misión Simulada en Vivo y Herramientas de Demo

### Cómo se solucionó (`commits 0d3a952`, `c5eec69`, `f73798b`, `a798de4`, `e985290`, `aa26860`, `f8a3cec`)
1. **Misión simulada en vivo (`POST /api/demo/simulacion/iniciar`, `GET /api/demo/simulacion/estado`, `POST /api/demo/simulacion/detener`):**
   - Corre en segundo plano una historia de **34 minutos de misión** (en ~2.5 minutos reales) enviando muestras por el canal de flujo continuo: entrega el resumen diario de sueño ARCHeR → sube el CO₂ de cabina → la línea base personal de T1 avisa en amarillo antes que las reglas fijas → T2 empeora y salta la **alerta colectiva** → cae el enlace por conjunción solar → T1 cae en **rojo** en pleno apagón → vuelve el enlace, **lo rutinario se compacta en un resumen** y salen primero las urgencias → se repara el aire y todos vuelven a verde (mientras en T4 la mediana absorbe un golpe falso de muñeca de 124 lpm).
2. **Simulador de dispositivo portátil con 7 perfiles (`POST /api/demo/sensor/{tid}`, `backend/app/fuentes/dispositivo_simulado.py`):**
   - Permite probar `estable`, `deterioro_respiratorio`, `exposicion_radiacion`, `proceso_infeccioso`, `intolerancia_ortostatica`, `hipoglucemia` e `hipoxia_ambiental_o2`.
3. **Escenarios instantáneos (`GET /api/demo/escenarios` y `POST /api/demo/escenarios/{nombre}`):** `hipoxia_eclipse`, `co2_colectivo`, `o2_colectivo` y `proceso_infeccioso`.
4. **Comparativa "Con ORBIT vs Sin ORBIT" (`GET /api/demo/comparativa`)** y **Calibración con PhysioNet BIDMC (`backend/app/fuentes/calibracion.py`)**.

---

## 4. Pruebas Automáticas que Vigilan la Seguridad y la Documentación

### Cómo se solucionó (`commits 213d8c1`, `2a318fc`, `99e59da`)
En `backend/tests/test_documentacion.py`, `backend/tests/test_seguridad_ia.py` y `backend/tests/test_pwa.py`:
- **Candado automático de rutas públicas:** recorre las **64 operaciones de la API** con la autenticación activada para garantizar que solo las 13 rutas declaradas en `RUTAS_PUBLICAS` respondan sin sesión.
- **Referencia de la API autogenerada (`scripts/generar_api_doc.py`):** genera [API_REFERENCIA.md](../../docs/API_REFERENCIA.md) directamente desde el código real.
- **Verificación de la verdad en los documentos:** comprueba que todas las rutas `/api/...` mencionadas en los `.md` existan en OpenAPI, que ningún enlace local esté roto, que todas las variables `ORBIT_*` estén en `.env.example` y que las cifras de cobertura del HRP coincidan con el código.

---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Antigravity (Google DeepMind)** sobre base técnica documentada con **Claude (Anthropic / Claude Code)**.
> - **Justificación de uso:** Se utilizó para estructurar y explicar en lenguaje claro y sin tecnicismos la arquitectura y los módulos del backend a partir del código fuente y el historial de commits, bajo la definición conceptual y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
