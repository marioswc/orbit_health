PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS tripulantes (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    creado_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    indicador TEXT NOT NULL,
    valor REAL NOT NULL,
    unidad TEXT NOT NULL,
    nivel TEXT NOT NULL CHECK (nivel IN ('verde','amarillo','rojo')),
    puntos_news2 INTEGER NOT NULL DEFAULT 0,
    origen TEXT NOT NULL CHECK (origen IN ('sensor','manual','calibracion','simulado')),
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cola_salida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    tipo_evento TEXT NOT NULL,
    prioridad INTEGER NOT NULL CHECK (prioridad IN (1,2,3)),
    payload TEXT NOT NULL,
    ts_guardado TEXT NOT NULL,
    hash_prev TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE,
    estado TEXT NOT NULL DEFAULT 'retenido' CHECK (estado IN ('retenido','en_transito','recibido')),
    transmitido_ts TEXT,
    llegada_estimada_ts TEXT,
    ack_estimado_ts TEXT,
    resumido INTEGER NOT NULL DEFAULT 0   -- 1 = evento de rutina cubierto por un resumen; sigue guardado, no se envía aparte
);

-- Sin relación con cola_salida por diseño.
CREATE TABLE IF NOT EXISTS diario_privado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    titulo TEXT,
    contenido TEXT NOT NULL,
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tamizajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    item1 INTEGER NOT NULL CHECK (item1 BETWEEN 0 AND 3),
    item2 INTEGER NOT NULL CHECK (item2 BETWEEN 0 AND 3),
    total INTEGER NOT NULL,
    riesgo_autolesion INTEGER NOT NULL DEFAULT 0 CHECK (riesgo_autolesion IN (0, 1)),
    calidad_oxigeno REAL,
    nivel_protocolo TEXT NOT NULL DEFAULT 'ninguno' CHECK (nivel_protocolo IN ('ninguno', 'seguimiento', 'crisis')),
    ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capsulas (
    id TEXT PRIMARY KEY,
    categoria TEXT NOT NULL,
    titulo TEXT NOT NULL,
    contenido_markdown TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lecturas_trip_ts ON lecturas (tripulante_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_cola_despacho ON cola_salida (estado, prioridad ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_cola_llegada ON cola_salida (estado, llegada_estimada_ts);
CREATE INDEX IF NOT EXISTS idx_diario_trip ON diario_privado (tripulante_id, ts DESC);

-- Estado del enlace persistente: sobrevive a reinicios del servidor.
CREATE TABLE IF NOT EXISTS estado_enlace (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    activo INTEGER NOT NULL,
    entorno TEXT NOT NULL
);
INSERT OR IGNORE INTO estado_enlace (id, activo, entorno) VALUES (1, 1, 'marte');

-- Seguridad local: credenciales por tripulante, sesiones persistentes y auditoría encadenada.
CREATE TABLE IF NOT EXISTS credenciales (
    tripulante_id TEXT PRIMARY KEY REFERENCES tripulantes(id) ON DELETE CASCADE,
    rol TEXT NOT NULL CHECK (rol IN ('tripulante','medico','comandante')),
    pin_salt TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    recup_salt TEXT NOT NULL,
    recup_hash TEXT NOT NULL,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TEXT,
    actualizado_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sesiones (
    token_hash TEXT PRIMARY KEY,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    creada_ts TEXT NOT NULL,
    expira_ts TEXT NOT NULL,
    revocada INTEGER NOT NULL DEFAULT 0
);

-- Mismas columnas que la cola para reutilizar la verificación de la cadena de hash.
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL,        -- quién actuó ('sistema' si no hay autenticación)
    tipo_evento TEXT NOT NULL,          -- acción
    prioridad INTEGER NOT NULL DEFAULT 0,
    payload TEXT NOT NULL,              -- JSON con objetivo y detalle
    ts_guardado TEXT NOT NULL,
    hash_prev TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE
);

-- Ánimo diario (1 a 5): privado como el PHQ-2; nunca entra a la cola de salida.
CREATE TABLE IF NOT EXISTS animo_diario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    valor INTEGER NOT NULL CHECK (valor BETWEEN 1 AND 5),
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_animo_trip_ts ON animo_diario (tripulante_id, ts DESC);

-- Preferencias que el propio astronauta elige para adaptar el asistente (no se deduce nada de su diario ni de su ánimo).
CREATE TABLE IF NOT EXISTS preferencias (
    tripulante_id TEXT PRIMARY KEY REFERENCES tripulantes(id) ON DELETE CASCADE,
    tono TEXT NOT NULL DEFAULT 'directo' CHECK (tono IN ('directo','calido')),
    detalle TEXT NOT NULL DEFAULT 'completo' CHECK (detalle IN ('breve','completo')),
    recordatorios TEXT NOT NULL DEFAULT 'normal' CHECK (recordatorios IN ('minimo','normal','frecuente')),
    actualizado_ts TEXT NOT NULL
);

-- Avisos internos al médico de a bordo con consentimiento explícito del propio tripulante.
-- Sin relación con cola_salida: nunca se transmiten a Tierra ni forman parte del informe exportable.
CREATE TABLE IF NOT EXISTS avisos_salud_mental (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripulante_id TEXT NOT NULL REFERENCES tripulantes(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('crisis', 'tamizaje_positivo')),
    nivel_protocolo TEXT NOT NULL CHECK (nivel_protocolo IN ('seguimiento', 'crisis')),
    tamizaje_id INTEGER REFERENCES tamizajes(id) ON DELETE SET NULL,
    mensaje_opcional TEXT,
    consentimiento INTEGER NOT NULL DEFAULT 1 CHECK (consentimiento = 1),
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'atendido', 'revocado')),
    atendido_por TEXT REFERENCES tripulantes(id),
    creado_ts TEXT NOT NULL,
    actualizado_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_avisos_sm_estado ON avisos_salud_mental (estado, creado_ts DESC);
