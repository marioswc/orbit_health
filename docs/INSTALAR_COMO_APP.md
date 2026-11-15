# ORBIT Health como app instalable (PWA) y en contenedor

## Qué es
Una **web app instalable**: se abre en su propia ventana, con icono, sin barra del navegador, y la pantalla carga aunque el servidor tarde. Es una PWA (manifiesto + service worker), no una app de tienda.

## Cómo se instala
| Dispositivo | Pasos |
|---|---|
| Chrome o Edge en computadora | Abre `http://127.0.0.1:3000` → aparece el aviso **"Instalar"** de ORBIT (o el icono de instalar en la barra de direcciones) |
| Android (Chrome) | Aviso **"Instalar"** de ORBIT, o menú ⋮ → *Instalar aplicación* |
| iPhone o iPad (Safari) | Botón compartir → *Agregar a pantalla de inicio* (Safari no muestra aviso propio) |
| Firefox de computadora | No instala PWA; sigue funcionando como página |

Atajos al mantener pulsado el icono (donde el sistema lo permita): **Monitor**, **Nova, mi compañía** y **Enlace con la Tierra**.

## Condición importante: HTTPS o localhost
Los navegadores solo permiten instalar y usar service worker en **`localhost`/`127.0.0.1` o con HTTPS**. Por HTTP simple en la red de la cabina (`http://192.168.x.x:3000`) **no se instala**; la web funciona igual. Para instalar desde otros dispositivos hace falta poner un proxy con TLS delante (por ejemplo Caddy con certificado interno). **No está incluido ni probado.**

## Qué hace sin conexión
- La interfaz (la "carcasa") se guarda en el dispositivo: se abre aunque el servidor tarde o esté apagado. Si no hay ninguna copia, muestra una pantalla "sin conexión" en español e inglés con botón de reintentar.
- **Los datos clínicos nunca se guardan en el navegador**: todo `/api` va siempre al servidor. Sin servidor, la app abre pero no muestra datos. Eso es deliberado: así nunca se ve un estado viejo como si fuera actual.
- Los archivos con hash en el nombre (`/assets/…`) se guardan para siempre; la página, el manifiesto y el service worker se revalidan cada vez (`Cache-Control: no-cache`).

## Actualizaciones
El service worker busca una versión nueva cada hora y al abrir. Cuando hay una, aparece **"Hay una versión nueva de ORBIT · Actualizar"**; al pulsar, se activa y recarga. No se actualiza sola a mitad de una captura.

## En un contenedor (Docker)
```bash
docker compose up --build        # http://127.0.0.1:3000, solo accesible desde este equipo
# o sin compose:
docker build -t orbit-health .
docker run -p 127.0.0.1:3000:3000 -v orbit-data:/app/data orbit-health
```
La imagen (≈ 180 MB) compila la interfaz y corre la API como usuario sin privilegios, con chequeo de salud y los datos en un volumen (`/app/data`). El puerto se publica solo en loopback a propósito: los datos de salud no se exponen en la red.
**Límite:** dentro del contenedor **no hay IA generativa local** (el proyecto solo acepta un modelo en loopback y Ollama queda fuera del contenedor); Nova responde con textos escritos. Para IA local usa la instalación normal (`scripts/asistente_inicio.sh`).

## Comprobaciones hechas y no hechas
- Hecho: pruebas automáticas del manifiesto (campos, iconos PNG con su tamaño real, atajos a pestañas que existen), del service worker (no guarda `/api`, precarga archivos que existen) y de las cabeceras de caché; el servidor sirve todos los archivos; la imagen de Docker se construyó, arrancó, quedó *healthy*, corre sin root y sirve la API y la interfaz.
- **No hecho:** instalar la app en un navegador real, probar el modo sin conexión y la pantalla de actualización en un dispositivo, medir con Lighthouse, ni capturas de pantalla en el manifiesto. Hay que probarlo a mano en Chrome o Edge.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación técnica, registrar las decisiones de arquitectura y mantener la trazabilidad con el código fuente y las fuentes públicas de la NASA, bajo la definición conceptual, revisión y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
