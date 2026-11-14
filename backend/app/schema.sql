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
    llegada_estimada_ts TEXT
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
CREATE INDEX IF NOT EXISTS idx_diario_trip ON diario_privado (tripulante_id, ts DESC);

-- Estado del enlace persistente: sobrevive a reinicios del servidor.
CREATE TABLE IF NOT EXISTS estado_enlace (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    activo INTEGER NOT NULL,
    entorno TEXT NOT NULL
);
INSERT OR IGNORE INTO estado_enlace (id, activo, entorno) VALUES (1, 1, 'marte');
