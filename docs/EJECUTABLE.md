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

## Para quien lo construye
```bash
scripts/crear_ejecutable.sh          # construye el de ESTE sistema: dist-ejecutable/orbit-health (+ .sha256)
```
Un ejecutable solo corre en el sistema donde se construyó. Para Windows y Mac está el flujo `.github/workflows/ejecutables.yml` (Actions → *Ejecutables* → *Run workflow*): construye los tres y los deja como artefactos; **no publica nada**.

## Comprobado y no comprobado
- Hecho (Linux): se construyó; arrancó en 1.8 s con una carpeta de datos nueva; sirvió API, interfaz y manifiesto; creó la base y los respaldos en la carpeta del usuario; ignoró un `.env` ajeno del directorio temporal; leyó el `.env` propio; detectó una instancia ya abierta; pruebas automáticas del lanzador.
- **No hecho:** el doble clic desde el explorador de archivos (se probó desde la terminal y sin abrir el navegador), el aspecto en Windows y Mac, el flujo de GitHub Actions, la firma de código y la notarización de Apple (cuestan dinero y cuentas de desarrollador), ni un instalador (`.msi`, `.dmg`, `.deb`).
