# 02 — Banda de Muñeca y Simulación en Vivo

## Qué problema había
Originalmente la aplicación dependía de un botón flotante de **"Captura manual"** para meter datos a mano, lo cual no refleja cómo funciona una tripulación usando un reloj o banda biométrica (como un dispositivo de actigrafía y pulso). Además, en pruebas anteriores no quedaba suficientemente claro cuándo un dato venía de un sensor real y cuándo de una simulación.

## Cómo se resolvió
- **Nueva vista de Banda con reloj interactivo 3D ([BandaPage.tsx](../../src/features/banda/routes/BandaPage.tsx), [RelojBanda.tsx](../../src/features/banda/components/RelojBanda.tsx), commits `c413dee`, `8573833`, `64c209f`, `feef45a`):**
  - Se creó una pestaña dedicada que representa el reloj/banda del astronauta en pantalla, con giro 3D, correa completa y soporte táctil para deslizar entre pantallas con el dedo.
  - Muestra en tiempo real las lecturas del tripulante y su racha de mediciones.
- **Eliminación de la Captura Manual en la interfaz principal ([App.tsx](../../src/app/App.tsx), commit `4e32de8`):**
  - Se quitó el botón flotante de `+ Captura manual` y su cajón lateral para que toda la experiencia gire en torno a lecturas automáticas provenientes de la banda (vía Bluetooth/puente) o de la simulación en vivo.
- **Transparencia de origen `simulado` ([SimuladorDemo.tsx](../../src/features/enlace/components/SimuladorDemo.tsx), commit `a0e80ab`):**
  - Los textos e indicadores del simulador aclaran explícitamente que las lecturas generadas para demostración tienen origen **simulado**, diferenciándolas de lecturas de un sensor físico.
