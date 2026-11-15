# ORBIT Health como ejecutable (doble clic)

Un solo archivo (≈ 24 MB en Linux) que lleva dentro el servidor, la interfaz y los datos del sistema. **No hace falta instalar Python ni Node.** Arranca en unos 2 segundos, abre el navegador y listo.

## Para quien lo usa
1. Descarga el archivo de tu sistema (`orbit-health` en Linux y Mac, `orbit-health.exe` en Windows) y su `.sha256` si quieres comprobar que no se alteró.
2. Dale doble clic. Se abre una ventana negra (no la cierres: es el programa) y el navegador en `http://127.0.0.1:3000`. La primera vez aparece la guía de bienvenida.
3. Para detenerlo, cierra esa ventana.

| Sistema | Lo que verás la primera vez |
|---|---|
| **Windows** | SmartScreen avisa "Windows protegió su PC" porque el archivo **no está firmado**: *Más información → Ejecutar de todos modos* |
| **Mac** | Gatekeeper lo bloquea por no estar firmado: clic derecho → *Abrir* → *Abrir* |
| **Linux** | Primero hay que darle permiso: `chmod +x orbit-health` (o clic derecho → Propiedades → Permisos → *Permitir ejecutar*) y luego doble clic o `./orbit-health` |

## Dónde guarda tus datos
En **tu** carpeta de usuario, nunca dentro del programa: Linux `~/.local/share/orbit-health`, Mac `~/Library/Application Support/ORBIT Health`, Windows `%LOCALAPPDATA%\ORBIT Health` (base de datos, respaldos y, si lo creas, un archivo `.env` con tu configuración). Actualizar el programa no toca tus datos. Para quitarlo todo: borra el archivo y esa carpeta.

## Qué trae y qué no
- Trae: monitor, semáforo, enlace con la Tierra, bienestar, Nova con textos escritos, guía de bienvenida, y la app instalable (PWA) funciona desde `127.0.0.1`.
- **No trae** la voz sin internet ni el modelo de IA local (pesan 0.5 GB y 1 GB). Si ya tienes Ollama instalado en tu computadora, el ejecutable lo usa solo si lo configuras en el `.env` de tu carpeta de datos. Para voz e IA: instalación normal con `scripts/asistente_inicio.sh`.
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
- **No hecho:** abrir el ejecutable de **Windows o Mac con doble clic en una computadora real** (la prueba de humo en GitHub lo arranca por línea de comandos y sin navegador); ver cómo se ve la interfaz en esos sistemas; Macs con procesador Intel (el construido es Apple Silicon); firma de código y notarización de Apple (cuestan dinero y cuentas de desarrollador); instaladores (`.msi`, `.dmg`, `.deb`). Los avisos de seguridad de la primera ejecución en Windows y Mac son esperables.
