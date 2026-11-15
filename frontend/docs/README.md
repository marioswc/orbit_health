# ORBIT Health — Documentación de Frontend

[English version](./README.en.md)

Interfaz web local de apoyo a la decisión clínica para tripulaciones en misiones de espacio profundo con comunicación degradada. Opera 100 % sin conexión a internet y está disponible en **español (`ES`)** e **inglés (`EN`)**.

---

## 1. Stack técnico y principios

- **Framework:** React 18 + TypeScript 5
- **Empaquetador y servidor de desarrollo:** Vite 5 (`@vitejs/plugin-react`)
- **Pruebas:** Vitest + Testing Library (`@testing-library/react`, `jsdom`)
- **Estilos:** CSS nativo consolidado en [`src/shared/styles/styles.css`](../src/shared/styles/styles.css) con soporte de tema **claro / oscuro**, adaptación por nivel de rendimiento (`data-rendimiento`), barra superior tipo hielo esmerilado, menú lateral transparente y tarjetas liquid glass.
- **Internacionalización (`i18n`):** Diccionarios locales en `src/i18n/locales/{ES,EN}/` con cambio en caliente desde la barra superior (`CambioIdioma`).
- **Regla de oro (100 % offline):**
  - El build de producción (`frontend/dist/`) se sirve directamente desde FastAPI sin conexión a internet.
  - Todas las fuentes (`Inter`, `Geist Mono`), iconos SVG, imágenes `.webp` y el Service Worker (`public/sw.js`) son locales. Prohibido usar CDNs o peticiones fuera de `/api`.

---

## 2. Entorno de desarrollo y comandos

Desde la carpeta `frontend/`:

```bash
# Instalar dependencias
pnpm install   # o npm install

# Servidor de desarrollo en http://localhost:3000
# Redirige /api/* -> http://localhost:8000 (ver vite.config.ts)
npm run dev

# Verificar tipos TypeScript y generar build estático en frontend/dist/
npm run build

# Medir presupuesto de tamaño del bundle (JS, CSS e imágenes)
npm run perf

# Correr todas las pruebas unitarias (31 archivos, 139 tests)
npx vitest run
```

> **Nota:** Para usar `npm run dev`, el backend debe correr en el puerto `8000`:
> ```bash
> cd backend && uvicorn app.main:app --reload --port 8000
> ```

---

## 3. Estructura de archivos (`frontend/src/`)

Arquitectura por features (*Screaming Architecture*):

```text
frontend/src/
├── app/                          # Shell principal: App.tsx, BarraLateral, AsistenteFlotante, rutas
├── features/
│   ├── asistente/                # Chat privado con Nova (saludo, atajos, historial corto, perfil IA)
│   ├── banda/                    # Reloj 3D interactivo (RelojBanda), misión simulada y racha
│   ├── bienestar/                # Ánimo diario, diario privado, tamizaje PHQ-2, protocolo de crisis y preferencias
│   ├── bienvenida/               # Guía de bienvenida paso a paso para nuevos tripulantes
│   ├── cabina/                   # Lecturas ambientales de cabina (CO₂ y dosis de radiación)
│   ├── enlace/                   # Consola de enlace Luna/Marte, Modo Eclipse, cola SHA-256, Tierra e informes CSV
│   ├── historial/                # Tabla filtrable y exportable de mediciones históricas
│   ├── mediciones/               # Panel de captura manual de signos vitales
│   ├── monitor/                  # Vista clínica principal: figura humana (.webp), NEWS2, zonas y signos vitales
│   ├── peligros/                 # Marco de riesgos NASA HRP (radiación, gravedad alterada, aislamiento)
│   ├── seguridad/                # AccesoTripulante (Tierra 3D, login por PIN, recuperación) y PerfilMenu
│   ├── sistema/                  # Estado de base de datos, respaldos, reinicio de PIN, avisos y auditoría
│   ├── tripulantes/              # Selector de tripulante activo
│   └── voz/                      # Burbuja de voz bilingüe ES/EN (Whisper/Piper local o Web Speech API)
├── i18n/                         # Motor i18n y locales ES / EN por feature
├── shared/                       # api/client.ts, componentes UI, hooks (useTema), rendimiento y styles/styles.css
└── main.tsx                      # Arranque de rendimiento, tema, i18n, Service Worker y React
```

---

## 4. Vistas y funcionalidades principales

1. **Acceso y perfil (`seguridad`)**: Pantalla de inicio de sesión sobre `Tierra3D`, autenticación por PIN, recuperación y cierre de sesión desde `PerfilMenu` en la barra superior.
2. **Bienvenida (`bienvenida`)**: Guía inicial paso a paso para tripulantes que entran por primera vez.
3. **Monitor (`monitor` + `cabina` + `mediciones`)**: Anillo NEWS2, figura humana interactiva con capas realistas `.webp` (traje, esqueleto, músculos, órganos), tarjetas de signos vitales, gráfica de series, acciones clínicas y captura manual.
4. **Banda (`banda`)**: Reloj 3D manipulable (`RelojBanda`), simulación de misión en vivo con eventos y racha de mediciones.
5. **Historial (`historial`)**: Registro histórico de lecturas por indicador y tripulante.
6. **Bienestar (`bienestar` + `voz`)**: Registro de ánimo, diario 100 % local, tamizaje PHQ-2, protocolo de crisis con consentimiento y asistente de voz.
7. **Asistente (`asistente`)**: Conversación privada con **Nova** (saludo contextual, atajos rápidos, memoria corta, perfil personal de intereses y rasgos). También accesible desde el botón flotante (`AsistenteFlotante`).
8. **Riesgos (`peligros`)**: Resumen de los riesgos fisiológicos y psicológicos del vuelo espacial.
9. **Enlace (`enlace`)**: Simulación Luna/Marte, Modo Eclipse, cola por prioridad con verificación de cadena de hashes, vista de mensajes recibidos en Tierra y descarga de informes CSV.
10. **Sistema (`sistema`)**: Salud del servidor y respaldos, reinicio de PIN por comandante, avisos de salud mental compartidos y verificación de auditoría.

---

## 5. Documentos relacionados

- [English documentation](./README.en.md)
- [API consumida por el frontend](./API.md)
- [Arquitectura](./ARQUITECTURA.md)
- [Estilo de la plataforma](./ESTILO_PLATAFORMA.md)
- [Figura humana](./FIGURA_HUMANA.md)
- [Uso de IA y documentación](./USO_IA_Y_DOCUMENTACION_FRONTEND.md)

---

## 6. Justificación y transparencia del uso de IA

De acuerdo con las reglas del **NASA Space Apps Challenge**, las herramientas de IA se utilizaron únicamente como **apoyo técnico** (implementación de componentes/hooks, estilos CSS, pruebas unitarias y redacción documental), bajo diseño, decisiones de producto y validación humana del equipo. Ver detalle completo en [USO_IA_Y_DOCUMENTACION_FRONTEND.md](./USO_IA_Y_DOCUMENTACION_FRONTEND.md) y [docs/SI_DISCLOSURE.md](../../docs/SI_DISCLOSURE.md).


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
