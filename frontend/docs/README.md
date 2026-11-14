# ORBIT Health — Documentación de Frontend

Interfaz local de apoyo a la decisión clínica para tripulaciones en misiones de espacio profundo con comunicación degradada.

---

## 1. Stack técnico y principios

- **Framework:** React 18 + TypeScript 5
- **Empaquetador y servidor de desarrollo:** Vite 5 (`@vitejs/plugin-react`)
- **Estilos:** CSS nativo con variables en `src/styles.css` (tema oscuro de cabina, sin frameworks CSS externos)
- **Regla de oro (100 % offline):**
  - El build de producción (`frontend/dist/`) se sirve directamente desde FastAPI sin conexión a internet.
  - **Prohibido** incluir fuentes remotas (p. ej. Google Fonts), iconos por CDN, scripts externos o peticiones fuera de `/api`.

---

## 2. Entorno de desarrollo y comandos

Desde la carpeta `frontend/`:

```bash
# Instalar dependencias (solo una vez con red)
npm install

# Servidor de desarrollo en http://localhost:3000
# Redirige automáticamente /api/* -> http://localhost:8000 (ver vite.config.ts)
npm run dev

# Verificar tipos TypeScript y generar build estático en frontend/dist/
npm run build

# Previsualizar el build estático en el puerto 3000
npm run preview
```

> **Nota:** Para usar `npm run dev`, el backend debe estar corriendo en otra terminal en el puerto `8000`:
> ```bash
> cd backend && uvicorn app.main:app --reload --port 8000
> ```

---

## 3. Estructura de archivos (`frontend/src/`)

```text
frontend/
├── docs/
│   └── README.md                  # Esta documentación
├── index.html                     # Punto de entrada HTML
├── package.json                   # Scripts y dependencias
├── tsconfig.json                  # Configuración de TypeScript
├── vite.config.ts                 # Puerto 3000 y proxy /api -> localhost:8000
└── src/
    ├── main.tsx                   # Montaje de React en #root
    ├── App.tsx                    # Layout principal, selector de tripulante y navegación por vistas
    ├── styles.css                 # Variables CSS, layout, badges y animaciones del mapa anatómico
    ├── api/
    │   ├── client.ts              # Wrapper fetch() hacia /api con manejo de errores HTTP
    │   └── tipos.ts               # Interfaces TypeScript compartidas con la API
    └── components/
        ├── FiguraHumana.tsx       # Mapa anatómico SVG por zonas corporales
        ├── PanelMedicion.tsx      # Captura manual de signos vitales y variables ambientales
        ├── DiarioTripulante.tsx   # Notas personales privadas (100 % locales, fuera de cola)
        ├── Tamizaje.tsx           # Cuestionario PHQ-2 confidencial y cápsulas de apoyo
        └── ConsolaEnlace.tsx      # Simulación Luna/Marte, Modo Eclipse, cola por prioridad y verificación SHA-256
```

---

## 4. Vistas y componentes

### 4.1 `App.tsx` (Contenedor principal)
- Carga la lista de tripulantes (`GET /api/tripulantes`) y el estado de validación de los umbrales (`GET /api/umbrales`).
- Muestra un banner de advertencia si los umbrales no están marcados como `validado`.
- Gestiona 3 vistas mediante pestañas:
  1. **Monitor (`vista === "monitor"`)**: Renderiza `FiguraHumana`, `PanelMedicion` y el panel de **Resumen** (puntaje NEWS2 en ventana vigente, variables faltantes y lista de últimos indicadores con su nivel).
  2. **Bienestar (`vista === "bienestar"`)**: Renderiza `DiarioTripulante` y `Tamizaje`.
  3. **Enlace (`vista === "enlace"`)**: Renderiza `ConsolaEnlace`.

### 4.2 `FiguraHumana.tsx` (Mapa anatómico SVG)
Agrupa las lecturas vigentes del tripulante en 5 zonas anatómicas y colorea cada región SVG con el peor nivel registrado (`verde`, `amarillo`, `rojo` o `sin_datos`):

| ID Zona | Etiqueta | Indicadores asociados |
|---|---|---|
| `snc` | Cabeza / SNC | `avpu` |
| `cardio` | Cardiovascular | `presion_sistolica`, `presion_diastolica`, `frecuencia_cardiaca` |
| `resp` | Respiratorio | `spo2`, `frecuencia_respiratoria` |
| `metab` | Tronco / Metabólico | `glucosa`, `temperatura` |
| `extr` | Extremidades | *(sin indicador asignado en el prototipo)* |

### 4.3 `PanelMedicion.tsx` (Captura manual)
- Obtiene el catálogo de indicadores y sus rangos fisiológicos válidos desde `GET /api/indicadores`.
- Valida en cliente que el valor numérico esté dentro de `[min, max]` antes de enviarlo (para `avpu` presenta un selector `0: A`, `1: V`, `2: P`, `3: U`).
- Envía `POST /api/lecturas` y muestra el resultado inmediato: nivel asignado, puntos NEWS2, prioridad en cola (`1`–`3`), si es observación o si activó aviso por desviación de línea base (>2 DE en ventana de 14 días).
- Dispara el callback `alGuardar()` para refrescar el estado en `App.tsx`.

### 4.4 `DiarioTripulante.tsx` (Diario privado)
- Permite consultar (`GET /api/diario/{tid}`) y guardar (`POST /api/diario`) notas de texto libre con título opcional.
- Incluye la etiqueta visible de privacidad: *"Almacenamiento local seguro: desconectado de la telemetría externa"*.
- Nunca genera eventos en `cola_salida`.

### 4.5 `Tamizaje.tsx` (Tamizaje PHQ-2)
- Cuestionario de 2 preguntas con escala `0` (*Nunca*) a `3` (*Casi todos los días*).
- Envía `POST /api/tamizajes` y recibe `{ total, positivo, capsulas }`.
- Si `total >= 3`, el tamizaje es positivo; muestra las cápsulas de autorregulación correspondientes. No encola eventos hacia Tierra.

### 4.6 `ConsolaEnlace.tsx` (Consola Store-and-Forward)
- Hace polling cada `2000 ms` a `GET /api/cola`.
- Permite alternar el entorno (`luna` con latencia de `1.3 s` vs. `marte` con `1200 s`) y el estado del enlace (`Enlace normal` vs. `Modo Eclipse`) vía `POST /api/enlace`.
- Muestra los eventos agrupados en 3 columnas por prioridad (`Prioridad 1 · rojo`, `Prioridad 2 · amarillo`, `Prioridad 3 · verde`) con su estado (`retenido`, `en_transito`, `recibido`).
- Incluye el botón **"Verificar cadena de hash"** (`GET /api/cola/verificar`) para comprobar la integridad criptográfica SHA-256 de la cola.

---

## 5. Contrato con la API del Backend

### 5.1 Endpoints consumidos actualmente

| Método y Ruta | Usado en | Respuesta principal |
|---|---|---|
| `GET /api/tripulantes` | `App.tsx` | `Tripulante[]` (`id`, `nombre`, `rol`) |
| `GET /api/umbrales` | `App.tsx` | `{ version, estado }` |
| `GET /api/estado/{tid}` | `App.tsx` | `Estado` (`indicadores`, `news2`, `nivel_general`, `ventana_min`, ...) |
| `GET /api/indicadores` | `PanelMedicion.tsx` | `IndicadorDef[]` (`clave`, `etiqueta`, `unidad`, `min`, `max`) |
| `POST /api/lecturas` | `PanelMedicion.tsx` | `RespuestaLectura` (`lectura_id`, `nivel`, `puntos_news2`, `prioridad`, ...) |
| `GET /api/diario/{tid}` | `DiarioTripulante.tsx` | `NotaDiario[]` |
| `POST /api/diario` | `DiarioTripulante.tsx` | `{ id }` |
| `POST /api/tamizajes` | `Tamizaje.tsx` | `RespuestaTamizaje` (`total`, `positivo`, `capsulas`) |
| `GET /api/cola` | `ConsolaEnlace.tsx` | `Cola` (`enlace`, `resumen`, `items`) |
| `POST /api/enlace` | `ConsolaEnlace.tsx` | `{ activo, entorno }` |
| `GET /api/cola/verificar` | `ConsolaEnlace.tsx` | `{ valida, total, primer_invalido }` |

### 5.2 Nuevas capacidades del Backend listas para integrar en el Frontend

Tras las últimas actualizaciones en `main`, el backend expone datos adicionales que podemos conectar en la interfaz:

1. **Frecuencia recomendada de captura (`proxima_captura_min`)**:
   - Devuelto tanto en `GET /api/estado/{tid}` como en `POST /api/lecturas`.
   - Valores: `60` min (verde), `15` min (amarillo), `5` min (rojo).
   - *Dónde mostrarlo:* en el panel de Resumen de `App.tsx` y en el mensaje de confirmación de `PanelMedicion.tsx`.

2. **Reglas combinadas individuales (`reglas_combinadas` y `nivel_fisiologico`)**:
   - Devueltos en `GET /api/estado/{tid}` y `POST /api/lecturas`.
   - Formato de cada regla activa: `{ id: string, nombre: string, nivel: Nivel }`.
   - *Dónde mostrarlo:* como alertas destacadas en la vista `Monitor` cuando se activa una combinación clínica (por ejemplo, cruce de signos vitales).

3. **Alerta colectiva de $\text{CO}_2$ en cabina (`GET /api/alertas/colectivas`)**:
   - Nuevo endpoint que cruza el nivel de $\text{CO}_2$ ambiental con el número de tripulantes con síntomas/afectación fisiológica:
     ```json
     {
       "activa": true,
       "nivel": "rojo",
       "co2_mmhg": 3.5,
       "tripulantes_afectados": ["t1", "t2"],
       "detalle": "CO2 elevado con varios tripulantes afectados"
     }
     ```
   - *Dónde mostrarlo:* como alerta global en el encabezado o en la vista `Monitor`.

---

## 6. Guía de estilos (`src/styles.css`)

### Variables CSS (`:root`)
- Fondos y bordes: `--bg` (`#0b1020`), `--panel` (`#151b30`), `--borde` (`#26304f`)
- Texto: `--texto` (`#e6e9f5`), `--suave` (`#98a2c3`), `--acento` (`#6c8cff`)
- Semáforo clínico:
  - `--verde`: `#2fbf71`
  - `--amarillo`: `#f2b84b`
  - `--rojo`: `#ef5350`
  - `--neutro`: `#3a4468` (sin datos)

### Clases principales
- `.grid`: rejilla responsiva (`repeat(auto-fit, minmax(300px, 1fr))`)
- `.panel`: tarjeta contenedora con fondo `--panel` y borde redondeado
- `.fila`: contenedor flex horizontal con `gap: 8px` y `flex-wrap: wrap`
- `.badge.<nivel>`: pastilla de estado (`.verde`, `.amarillo`, `.rojo`, `.sin_datos`)
- `.zona.<nivel>`: relleno de regiones SVG en `FiguraHumana` (incluye animación de parpadeo en `.amarillo` y `.rojo`)

---

## 7. Flujo de trabajo en Git (`dev-frontend`)

Rama de trabajo compartida para Frontend (Lourdes y Santi): `dev-frontend`.

```bash
# 1. Cambiar a la rama de frontend (si no estás en ella)
git checkout dev-frontend

# 2. Bajar los últimos cambios de tu compañero antes de empezar
git pull origin dev-frontend

# 3. Guardar y subir tus avances a dev-frontend
git add .
git commit -m "feat(front): descripción breve del cambio"
git push origin dev-frontend

# 4. Traer actualizaciones nuevas desde main hacia dev-frontend
git fetch origin
git merge origin/main
git push origin dev-frontend
```

