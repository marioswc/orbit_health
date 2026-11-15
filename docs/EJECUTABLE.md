# ORBIT Health como ejecutable (doble clic)

Un solo archivo (≈ 24 MB en Linux) que lleva dentro el servidor, la interfaz y los datos del sistema. **No hace falta instalar Python ni Node.** Arranca en unos 2 segundos, abre el navegador y listo.

## Para quien lo usa
1. Descarga el archivo de tu sistema (`orbit-health` en Linux y Mac, `orbit-health.exe` en Windows) y su `.sha256` si quieres comprobar que no se alteró.
2. Dale doble clic. Se abre **la ventana de ORBIT** (como una app: sin pestañas ni barra de direcciones, con su icono) y, por dentro, arranca el servidor. La primera vez aparece la guía de bienvenida.
3. Para detenerlo, **cierra la ventana de ORBIT**: el servidor se apaga solo.

**Cómo se hace la ventana:** usa el navegador basado en Chromium que ya traiga tu sistema, en *modo aplicación* y con un perfil propio (no toca tus pestañas ni tus sesiones): **Edge** en Windows (viene incluido en Windows 10 y 11), y Chrome, Edge, Chromium o Brave donde estén instalados en Linux y Mac. Si no hay ninguno (por ejemplo solo Firefox o Safari, que no tienen modo aplicación), abre el navegador normal y el servidor sigue hasta que lo detengas con Ctrl+C. Opciones: `--navegador` fuerza el navegador normal; `--sin-navegador` arranca solo el servidor.

**Windows:** el ejecutable se construye sin consola, así que no aparece ninguna ventana negra; si algo falla, queda escrito en `orbit-health.log` dentro de la carpeta de datos. **Mac:** se mantiene una ventana de Terminal detrás (convertirlo en un `.app` no se pudo probar).

| Sistema | Lo que verás la primera vez |
|---|---|
| **Windows** | SmartScreen avisa "Windows protegió su PC" porque el archivo **no está firmado**: *Más información → Ejecutar de todos modos* |
| **Mac** | Gatekeeper lo bloquea por no estar firmado: clic derecho → *Abrir* → *Abrir* |
| **Linux** | Primero hay que darle permiso: `chmod +x orbit-health` (o clic derecho → Propiedades → Permisos → *Permitir ejecutar*) y luego doble clic o `./orbit-health` |

## Paquete completo: la IA va dentro (sin Ollama, sin servidor aparte)
El ejecutable lleva **el motor de IA incrustado** (llama.cpp, dentro del mismo proceso). Falta el modelo, que pesa ~1.1 GB (Qwen2.5 1.5B Instruct, licencia Apache-2.0). Hay dos formas de tenerlo:

| Forma | Cómo |
|---|---|
| **Paquete completo** (todo en un archivo, sin internet) | `orbit-health-<sistema>-completo`: trae el ejecutable y la carpeta `modelos/`. Se descomprime y se abre. Se arma con `scripts/crear_paquete_completo.sh` |
| **Ejecutable solo** + modelo después | Una vez, con internet: `orbit-health --descargar-modelo`. Queda en tu carpeta de datos (`modelos/`) y el programa lo encuentra solo |

Qué hace el programa al arrancar: busca un `.gguf` en `modelos/` junto al programa y en tu carpeta de datos; si lo encuentra, **Nova responde con él, dentro del propio programa**, sin red, y **nada sale de la computadora** aunque haya una clave de nube configurada. Perfil, rasgos y conversación pueden usarse con él porque nunca salen del proceso. Si no hay modelo, Nova usa textos escritos.

Medido en Linux (CPU, 8 núcleos, sin GPU), con el modelo de 1.5B y Ollama desactivado a propósito: la primera respuesta tarda unos 5 a 16 s (carga el modelo y procesa la instrucción fija) y las siguientes unos 4 s. El motor suma ~26 MB al ejecutable (≈ 50 MB en total). La calidad es la de un modelo pequeño: acompaña y hace una pregunta, pero es limitado.

**Qué NO lleva todavía: la voz** (reconocimiento y síntesis). Eso es otra pila de librerías y modelos (≈ 0.6 GB) que no se pudo empaquetar ni probar dentro del ejecutable. La voz sigue necesitando la instalación normal (`scripts/instalar_voz_local.sh`).

## Dónde guarda tus datos
En **tu** carpeta de usuario, nunca dentro del programa: Linux `~/.local/share/orbit-health`, Mac `~/Library/Application Support/ORBIT Health`, Windows `%LOCALAPPDATA%\ORBIT Health` (base de datos, respaldos y, si lo creas, un archivo `.env` con tu configuración). Actualizar el programa no toca tus datos. Para quitarlo todo: borra el archivo y esa carpeta.

## Qué trae y qué no
- Trae: monitor, semáforo, enlace con la Tierra, bienestar, Nova (con la IA incrustada si hay modelo; con textos escritos si no), guía de bienvenida y la app instalable (PWA) desde `127.0.0.1`.
- **No trae la voz** sin internet. Si ya tienes Ollama, el ejecutable lo usa si lo configuras en el `.env` de tu carpeta de datos (el modelo incrustado tiene prioridad). Para la voz: instalación normal con `scripts/asistente_inicio.sh`.
- Solo escucha en `127.0.0.1`: nadie más en la red ve los datos. Si ya hay un ORBIT abierto, otro doble clic solo abre el navegador (no duplica).

## Seguridad al empaquetar
Dentro del ejecutable el programa **no busca nunca un `.env`** fuera de tu carpeta de datos (una carpeta temporal compartida podría tener uno ajeno). Hay una prueba que lo verifica y se comprobó con el ejecutable real.

## Cómo obtener los ejecutables de los tres sistemas
Un ejecutable solo corre en el sistema donde se construyó, así que los de Windows y Mac los construye GitHub:
1. En el repositorio: **Actions → Ejecutables → Run workflow** (rama `main`). Tarda unos 5 minutos.
2. Al terminar, en la página de la ejecución, sección **Artifacts**, se descargan `orbit-health-linux` (`.tar.gz`), `orbit-health-macos` (`.tar.gz`, **solo Apple Silicon**) y `orbit-health-windows` (`.zip`). Cada uno trae el programa y su `.sha256`. Los `.tar.gz` conservan el permiso de ejecución.
3. Cada sistema **construye y prueba su propio ejecutable** (`scripts/probar_ejecutable.sh`): lo arranca con una carpeta de datos aislada y comprueba API, interfaz, manifiesto, service worker, iconos, saludo de Nova, que crea sus datos en la carpeta del usuario y que no lee un `.env` ajeno. Si algo falla, el flujo se pone en rojo.

Los artefactos los puede descargar quien tenga acceso al repositorio y **caducan** (90 días por defecto). Para entregarlos a otras personas (por ejemplo, a los jueces) hay que subirlos a mano a un *Release* de GitHub: es una decisión del equipo y este flujo **no publica nada**.

## Para quien lo construye en su máquina
```bash
scripts/crear_ejecutable.sh          # construye el de ESTE sistema: dist-ejecutable/orbit-health (+ .sha256)
scripts/probar_ejecutable.sh         # prueba de humo del que acabas de construir
```

## Comprobado y no comprobado
- **Comprobado en GitHub (ejecución del 15-nov-2026):** los tres sistemas (Linux, Windows y macOS) construyeron el ejecutable y **pasaron la prueba de humo** corriéndolo allí mismo. Linux es el más probado: además se descargó el artefacto de GitHub, se verificó su suma, conserva el permiso de ejecución y pasó la prueba de humo en una computadora real.
- Hecho en Linux por mí: arranca en unos 2 s con una carpeta de datos nueva; creó la base y los respaldos en la carpeta del usuario; ignoró un `.env` ajeno; leyó el `.env` propio; detectó una instancia ya abierta.
- **IA incrustada (comprobado en Linux):** se construyó el ejecutable con el motor, se armó el paquete completo, se descomprimió en una carpeta limpia y Nova respondió con el modelo de dentro y Ollama desactivado. En Windows y Mac **no se probó**: el motor incrustado depende de que exista una rueda precompilada para ese sistema; si no, el ejecutable sale sin él (el script lo avisa).
- **Ventana de aplicación (comprobado en Linux con Edge):** se abre su propia ventana, y al cerrarla el servidor pasa de responder a apagado por sí solo.
- **No hecho:** la ventana de aplicación en **Windows y Mac** (la lógica está probada con pruebas automáticas, pero ahí solo corrió la prueba de humo del servidor, sin ventana); abrir el ejecutable de **Windows o Mac con doble clic en una computadora real** (la prueba de humo en GitHub lo arranca por línea de comandos y sin navegador); ver cómo se ve la interfaz en esos sistemas; Macs con procesador Intel (el construido es Apple Silicon); firma de código y notarización de Apple (cuestan dinero y cuentas de desarrollador); instaladores (`.msi`, `.dmg`, `.deb`). Los avisos de seguridad de la primera ejecución en Windows y Mac son esperables.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
