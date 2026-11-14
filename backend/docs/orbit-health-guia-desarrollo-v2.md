# ORBIT Health: Especificación Técnica y Arquitectura Maestra de Desarrollo

La plataforma ORBIT Health constituye un sistema de apoyo a la decisión clínica para misiones tripuladas de espacio profundo hacia Marte y la Luna, diseñado para operar en condiciones de comunicación degradada, latencia extrema y aislamiento operativo total. A diferencia de los entornos hospitalarios terrestres, donde la telemedicina depende de conexiones de banda ancha continuas y evacuación inmediata, una tripulación interplanetaria debe gestionar emergencias y monitoreo fisiológico de manera 100% autónoma. Este documento consolida la arquitectura técnica completa, el modelo de datos relacional, las reglas clínicas estandarizadas, el protocolo de resiliencia ante pérdidas de enlace y la guía de desarrollo paso a paso para la implementación del sistema.

--------------------------------------------------------------------------------

## 1. Fundamentación Operativa y Mapeo de Riesgos NASA HRP

Para que el software posea validez técnica ante evaluadores de agencias espaciales, cada funcionalidad debe responder directamente a los peligros y riesgos documentados por el Programa de Investigación Humana de la NASA (*Human Research Program*, HRP). El viaje interplanetario impone cinco peligros fundamentales que condicionan el diseño de la plataforma:

### Los Cinco Peligros Fundamentales de la NASA

1. **Radiación Espacial (*Space Radiation*):**
   * *Naturaleza del riesgo:* Fuera de la magnetosfera protectora de la Tierra, la tripulación se expone a radiación cósmica galáctica y eventos de partículas solares. Mientras que en la Estación Espacial Internacional (ISS) los astronautas reciben diez veces más radiación que en la superficie terrestre, en el espacio profundo la dosis acumulada es sustancialmente mayor y más destructiva.
   * *Impacto fisiológico:* Aumento significativo del riesgo de cáncer, daño al sistema nervioso central con alteraciones cognitivas, pérdida motora y cambios de comportamiento, además de riesgo cardiovascular, cataratas, náuseas, vómitos y fatiga.
   * *Respuesta en el software:* Monitoreo de dosimetría acumulada inspirado en instrumentos espaciales continuos como el espectrómetro canadiense CANS (*Canadian Active Neutron Spectrometer* de la Agencia Espacial Canadiense, CSA), calculando el porcentaje consumido del límite biológico de carrera de la misión.

2. **Aislamiento y Confinamiento (*Isolation & Confinement*):**
   * *Naturaleza del riesgo:* Confinamiento prolongado de grupos reducidos en habitáculos cerrados, sujetos a cargas de trabajo extenuantes alternadas con monotonía y falta de variedad en alimentos frescos.
   * *Impacto fisiológico:* Deterioro en la moral, dinamismo de equipo, interacción interpersonal y desregulación circadiana. En Marte, el ciclo diario añade aproximadamente treinta y ocho a treinta y nueve minutos de luz respecto a las veinticuatro horas terrestres, desestabilizando el sueño.
   * *Respuesta en el software:* Tamizaje estructurado de bienestar mental (PHQ-2), métricas de arquitectura de descanso y un módulo de diario personal privado desvinculado de la telemetría exterior, cumpliendo la directriz de la NASA sobre herramientas personales de desahogo.

3. **Distancia a la Tierra (*Distance From Earth*):**
   * *Naturaleza del riesgo:* Mientras que la Luna dista a 238,855 millas, Marte se sitúa a un promedio de 140 millones de millas. Esta separación geográfica anula toda posibilidad de misiones de reabastecimiento logístico o evacuación médica de urgencia.
   * *Impacto operativo:* Retardo de comunicaciones electromagnéticas de hasta 20 minutos en un solo sentido, generando una latencia mínima de 40 minutos en el ciclo completo de ida y vuelta.
   * *Respuesta en el software:* Autosuficiencia diagnóstica a bordo, almacenamiento local en SQLite y motor de triaje determinista inmediato que opera sin requerir confirmación desde el control de misión en Tierra.

4. **Campos Gravitatorios Variables (*Altered Gravity Fields*):**
   * *Naturaleza del riesgo:* La misión atraviesa tres entornos de gravedad: estándar terrestre de $1g$, ingravidez y microgravedad durante el tránsito interplanetario de seis meses, y gravedad parcial marciana de $3/8$ ($37.5\%$ de la terrestre).
   * *Impacto fisiológico:* Desadaptación sensorimotora que compromete la orientación espacial, la coordinación mano-ojo y el equilibrio; redistribución cefálica de fluidos corporales; y desmineralización ósea acelerada con pérdida ósea continua estimada entre el $1\%$ y el $1.5\%$ mensual, acompañada de atrofia muscular.
   * *Respuesta en el software:* Registro de protocolos de acondicionamiento físico, seguimiento de biomarcadores y calibración de líneas base individuales adaptadas a la permanencia en microgravedad.

5. **Entornos Cerrados y Hostiles (*Hostile/Closed Environments*):**
   * *Naturaleza del riesgo:* La nave constituye un sistema de soporte vital cerrado donde el aire y el agua deben reciclarse continuamente, reutilizando el dióxido de carbono y la orina de la tripulación. Los microbios transfieren y mutan con facilidad en ambientes cerrados herméticos.
   * *Impacto fisiológico:* Supresión del sistema inmunitario por estrés crónico y mayor vulnerabilidad a infecciones, alergias y acumulación de tóxicos ambientales.
   * *Respuesta en el software:* Monitoreo continuo de la calidad del aire de cabina (especialmente concentración de $\text{CO}_2$) y correlación automática entre las alertas ambientales colectivas y la sintomatología individual del tripulante.

### Cobertura de Riesgos HRP del Catálogo Oficial
El catálogo oficial del HRP contempla diecisiete riesgos. El sistema ORBIT Health vincula indicadores directos e indirectos a nueve de ellos:

| Grupo | Riesgos Cubiertos | Naturaleza del Indicador |
| :--- | :--- | :--- |
| Con indicador directo en plataforma | Cardiovascular, Hipoxia, Condición física, Masa ósea, Salud conductual, Sueño, Cáncer por radiación | Presión arterial, pulso, $\text{SpO}_2$, ejercicio, dosimetría continua, cuestionario anímico y registro circadiano |
| Con cobertura indirecta | Sistema inmune, Nutrición y metabolismo | Temperatura corporal (alerta inmunológica) y glucemia capilar (balance metabólico) |
| Asignados en cabina | Vestibular, Microbioma, Factor de equipo | Coordinación visuomotora, monitoreo de superficies y diario privado |
| Declarados fuera de alcance | Descompresión, Actividad extravehicular (EVA), SANS, Cargas dinámicas, Fallos estructurales de sistemas | Requieren telemetría biomecánica o instrumental no presente en el alcance del prototipo |

--------------------------------------------------------------------------------

## 2. Estrategia de Datos y Validación sin Telemetría Real

La ausencia de conjuntos de datos públicos de telemetría médica en vuelos a Marte es una constante metodológica: las misiones no han ocurrido y los registros médicos de tripulaciones espaciales en órbita terrestre son confidenciales. Superar esta condición requiere una estrategia rigurosa basada en datos humanos reales, motores deterministas y calibración de líneas base.

### Pilares de Validación

1. **Datos Fisiológicos Reales de PhysioNet:**  
   En lugar de generar números aleatorios sin coherencia biológica, el sistema se calibra con series temporales humanas de acceso abierto procedentes de PhysioNet. Estos registros aportan variabilidad fisiológica auténtica, ruido instrumental, respuestas hemodinámicas reales y correlaciones entre frecuencia respiratoria, saturación de oxígeno y pulso.

2. **Rechazo a Modelos de Caja Negra en Fase Crítica:**  
   La implementación de redes neuronales de aprendizaje en línea (*online learning*) dentro del bucle de decisión primaria en vuelo presenta barreras insalvables:
   * *Muestra mínima (Cold Start):* Con una tripulación de cuatro a seis astronautas, no existe volumen muestral suficiente para entrenar modelos predictivos fiables sin incurrir en sobreajuste severo.
   * *Opacidad y falta de auditabilidad:* Las agencias espaciales exigen algoritmos verificables y explicables. Un modelo que altera sus parámetros dinámicamente impide a los cirujanos de vuelo certificar la seguridad de los protocolos diagnósticos.

3. **Líneas Base Individuales Móviles:**  
   El software adopta el principio médico espacial de que el astronauta es su propio grupo de control. En lugar de comparar exclusivamente contra constantes fijas de adultos sanos a nivel del mar, el sistema construye una distribución móvil en el almacenamiento local SQLite:

   $$\mu_{14} = \frac{1}{N} \sum_{i=1}^{N} x_i \quad \text{y} \quad \sigma_{14} = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} (x_i - \mu_{14})^2}$$

   Las desviaciones estadísticas superiores a dos desviaciones estándar respecto a su promedio de catorce días en microgravedad activan avisos preventivos, identificando deterioros subclínicos antes de cruzar los límites de emergencia médica.

--------------------------------------------------------------------------------

## 3. Motor Clínico y Reglas de Decisión Estandarizadas

El motor de decisión clínica traduce las lecturas fisiológicas y ambientales en niveles de criticidad auditables mediante tres estándares transparentes:

### 1. Escala NEWS2 (*National Early Warning Score*) Adaptada
La escala del *Royal College of Physicians* (RCP) evalúa seis variables clave asignando puntuaciones de cero a tres según la gravedad del desvío:

| Variable Fisiológica | 3 Puntos | 2 Puntos | 1 Punto | 0 Puntos (Normal) | 1 Punto | 2 Puntos | 3 Puntos |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Frecuencia respiratoria (rpm) | $\le 8$ | — | 9–11 | 12–20 | — | 21–24 | $\ge 25$ |
| Saturación de $\text{O}_2$ ($\%$) | $\le 91$ | 92–93 | 94–95 | $\ge 96$ | — | — | — |
| Presión sistólica (mmHg) | $\le 90$ | 91–100 | 101–110 | 111–219 | — | — | $\ge 220$ |
| Frecuencia cardíaca (lpm) | $\le 40$ | — | 41–50 | 51–90 | 91–110 | 111–130 | $\ge 131$ |
| Nivel de conciencia (AVPU) | — | — | — | Alerta (A) | — | — | V, P o U |
| Temperatura corporal ($^\circ\text{C}$) | $\le 35.0$ | — | 35.1–36.0 | 36.1–38.0 | 38.1–39.0 | $\ge 39.1$ | — |

*Declaraciones de rigor técnico:*
* En la escala RCP oficial, una temperatura $\ge 39.1\ ^\circ\text{C}$ otorga 2 puntos (alerta moderada) y no dispara una alerta roja aislada directa. El sistema clasifica como alerta roja cuando la puntuación agregada es $\ge 7$ o cuando un parámetro vital alcanza 3 puntos de gravedad extrema.
* Umbrales de glucemia capilar: valores entre 100 y 125 mg/dL se catalogan como observación preventiva (criterio de alteración en ayunas), reservando alertas clínicas mayores para hipoglucemias severas o hiperglucemias extremas.
* Presión diastólica: valores $<60\text{ mmHg}$ se identifican como observación de perfusión pero se declaran expresamente en la documentación como supuestos de diseño sujetos a validación por un especialista médico de vuelo.

### 2. Tamizaje Psicológico PHQ-2
El cuestionario de dos preguntas de tamizaje evalúa el estado de ánimo de las últimas dos semanas en escala de 0 a 3:
1. Poco interés o placer en hacer las cosas.
2. Sentirse desanimado, deprimido o sin esperanza.

$$\text{Puntuación PHQ-2} = \text{Ítem}_1 + \text{Ítem}_2 \quad (\text{Rango } 0 \text{ a } 6)$$

*Manejo de confidencialidad:* Una puntuación $\ge 3$ se considera positiva para riesgo de distimia o depresión. El software no emite alertas públicas a la nave ni programa revisiones automáticas con el comandante, sino que ofrece discretamente recursos de autorregulación y cápsulas de apoyo en la interfaz personal del tripulante para salvaguardar la intimidad.

### 3. Parámetros de Calidad del Aire en Cabina
El monitoreo de la atmósfera en la nave espacial correlaciona los signos de la tripulación con el ambiente hermético:

* **Concentración de $\text{CO}_2$:**
  * Normal: $\le 3.0\text{ mmHg}$.
  * Alerta preventiva (Amarilla): $3.1\text{ a } 4.0\text{ mmHg}$ (indica saturación parcial de absorbedores de dióxido de carbono).
  * Alerta crítica (Roja): $> 4.0\text{ mmHg}$ (riesgo agudo de cefalea, narcosis por gas y acidosis respiratoria colectiva).
* **Radiación:** Seguimiento continuo expresado en porcentaje respecto al límite de dosis de carrera de la misión espacial, registrando incrementos que superen las tasas basales de tránsito interplanetario.

--------------------------------------------------------------------------------

## 4. Arquitectura de Base de Datos SQLite

La persistencia del software reside íntegramente en un archivo local SQLite (`orbit_health.db`). Esta decisión técnica garantiza latencias de lectura y escritura inferiores a diez milisegundos, cero dependencias de servicios externos y trazabilidad completa.

A continuación se detalla el esquema DDL estructurado para producción:

```sql
-- Habilitar integridad referencial y modo de escritura optimizado
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. Tabla de Tripulantes
CREATE TABLE IF NOT EXISTS astronautas (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    grupo_sanguineo TEXT NOT NULL,
    creado_ts DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Lecturas Fisiológicas y Ambientales
CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id TEXT NOT NULL,
    indicador TEXT NOT NULL,
    valor REAL NOT NULL,
    unidad TEXT NOT NULL,
    nivel_alerta TEXT CHECK(nivel_alerta IN ('verde', 'amarillo', 'rojo')) NOT NULL,
    puntuacion_news2 INTEGER DEFAULT 0,
    origen TEXT CHECK(origen IN ('sensor', 'manual', 'physionet', 'simulado')) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (astronauta_id) REFERENCES astronautas(id) ON DELETE CASCADE
);

-- 3. Cola de Transmisión hacia la Tierra (Store-and-Forward con Prioridad)
CREATE TABLE IF NOT EXISTS cola_tierra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id TEXT NOT NULL,
    tipo_evento TEXT NOT NULL,
    prioridad INTEGER NOT NULL CHECK(prioridad IN (1, 2, 3)), -- 1: Crítico/Rojo, 2: Preventivo/Amarillo, 3: Rutina/Verde
    hash_ancla TEXT,
    payload TEXT NOT NULL,
    creado DATETIME DEFAULT CURRENT_TIMESTAMP,
    transmitido DATETIME,
    llegada_estimada DATETIME,
    estado_envio TEXT CHECK(estado_envio IN ('retenido', 'en_transito', 'recibido')) NOT NULL DEFAULT 'retenido',
    FOREIGN KEY (astronauta_id) REFERENCES astronautas(id) ON DELETE CASCADE
);

-- 4. Diario Personal Privado (Estrictamente Desvinculado de la Cola de Salida)
CREATE TABLE IF NOT EXISTS diario_privado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    astronauta_id TEXT NOT NULL,
    titulo TEXT,
    contenido TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (astronauta_id) REFERENCES astronautas(id) ON DELETE CASCADE
);

-- 5. Tabla de Cápsulas y Guías de Soporte Clínico
CREATE TABLE IF NOT EXISTS capsulas (
    id TEXT PRIMARY KEY,
    categoria TEXT NOT NULL,
    titulo TEXT NOT NULL,
    contenido_markdown TEXT NOT NULL,
    nivel_acceso TEXT DEFAULT 'tripulante'
);

-- Índices de alto rendimiento para consultas clínicas y despacho de cola
CREATE INDEX IF NOT EXISTS idx_lecturas_ast_ts ON lecturas (astronauta_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cola_despacho ON cola_tierra (estado_envio, prioridad ASC, creado ASC);
CREATE INDEX IF NOT EXISTS idx_diario_ast ON diario_privado (astronauta_id, timestamp DESC);
```

--------------------------------------------------------------------------------

## 5. Implementación del Backend (Python / FastAPI)

El backend de ORBIT Health expone una interfaz REST ligera y determinista construida con FastAPI, orientada a la ejecución en local y sin conexión a internet.

### 1. Motor Clínico y Clasificación (`engine.py`)

```python
from typing import Dict, Any, Tuple

def evaluar_news2(signos: Dict[str, Any]) -> Tuple[int, str]:
    """
    Calcula la puntuación oficial NEWS2 adaptada y retorna (puntos_totales, nivel_alerta).
    """
    puntos = 0
    
    # 1. Frecuencia respiratoria
    fr = signos.get("frecuencia_respiratoria", 16)
    if fr <= 8 or fr >= 25:
        puntos += 3
    elif 21 <= fr <= 24:
        puntos += 2
    elif 9 <= fr <= 11:
        puntos += 1

    # 2. Saturación de Oxígeno (SpO2)
    spo2 = signos.get("spo2", 98)
    if spo2 <= 91:
        puntos += 3
    elif 92 <= spo2 <= 93:
        puntos += 2
    elif 94 <= spo2 <= 95:
        puntos += 1

    # 3. Presión Arterial Sistólica
    pas = signos.get("presion_sistolica", 120)
    if pas <= 90 or pas >= 220:
        puntos += 3
    elif 91 <= pas <= 100:
        puntos += 2
    elif 101 <= pas <= 110:
        puntos += 1

    # 4. Frecuencia Cardíaca (Pulso)
    fc = signos.get("frecuencia_cardiaca", 75)
    if fc <= 40 or fc >= 131:
        puntos += 3
    elif 111 <= fc <= 130:
        puntos += 2
    elif 41 <= fc <= 50 or 91 <= fc <= 110:
        puntos += 1

    # 5. Nivel de Conciencia (AVPU)
    avpu = signos.get("avpu", "A")
    if avpu != "A":
        puntos += 3

    # 6. Temperatura Corporal
    temp = signos.get("temperatura", 36.8)
    if temp <= 35.0:
        puntos += 3
    elif temp >= 39.1:
        puntos += 2
    elif (35.1 <= temp <= 36.0) or (38.1 <= temp <= 39.0):
        puntos += 1

    # Determinación de Nivel de Alerta
    if puntos >= 7 or any(
        (fr <= 8 or fr >= 25),
        (spo2 <= 91),
        (pas <= 90 or pas >= 220),
        (fc <= 40 or fc >= 131),
        (avpu != "A"),
        (temp <= 35.0)
    ):
        nivel = "rojo"
    elif puntos >= 5 or puntos in (1, 2, 3, 4):
        nivel = "amarillo" if puntos >= 5 else "verde"
    else:
        nivel = "verde"

    return puntos, nivel


def evaluar_ambiente(co2_mmhg: float, radiacion_pct: float) -> str:
    """
    Evalúa parámetros ambientales del habitáculo.
    """
    if co2_mmhg > 4.0 or radiacion_pct >= 90.0:
        return "rojo"
    elif 3.1 <= co2_mmhg <= 4.0 or radiacion_pct >= 70.0:
        return "amarillo"
    return "verde"
```

### 2. Despachador de Cola y Resiliencia en Modo Eclipse (`queue_manager.py`)

```python
import sqlite3
import hashlib
import json
import time
from datetime import datetime, timedelta

DB_PATH = "orbit_health.db"

# Latencias nominales NASA (en segundos)
LATENCIA_LUNA = 1.3
LATENCIA_MARTE = 1200.0  # 20 minutos
FACTOR_ACELERACION = 30.0  # 20 min se simulan en 40 segundos

class QueueManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def encolar_evento(self, astronauta_id: str, tipo_evento: str, prioridad: int, payload: dict) -> int:
        """
        Inserta un evento en la cola y calcula el hash encadenado con el registro anterior.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el hash del último evento registrado
            cursor.execute("SELECT hash_ancla FROM cola_tierra ORDER BY id DESC LIMIT 1")
            prev_row = cursor.fetchone()
            prev_hash = prev_row["hash_ancla"] if prev_row and prev_row["hash_ancla"] else "GENESIS_BLOCK_ORBIT"
            
            # Generar hash SHA-256 encadenado
            contenido = f"{prev_hash}|{astronauta_id}|{tipo_evento}|{prioridad}|{payload_str}|{time.time()}"
            nuevo_hash = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
            
            cursor.execute("""
                INSERT INTO cola_tierra (astronauta_id, tipo_evento, prioridad, hash_ancla, payload, estado_envio)
                VALUES (?, ?, ?, ?, ?, 'retenido')
            """, (astronauta_id, tipo_evento, prioridad, nuevo_hash, payload_str))
            
            conn.commit()
            return cursor.lastrowid

    def procesar_despacho(self, enlace_activo: bool, entorno: str = "marte") -> list:
        """
        Si hay enlace activo, transmite los mensajes respetando la prioridad médica estricta.
        En Modo Eclipse (enlace_activo=False), retiene y no transmite.
        """
        if not enlace_activo:
            return []  # Modo Eclipse: nada sale de la nave

        latencia_base = LATENCIA_MARTE if entorno.lower() == "marte" else LATENCIA_LUNA
        tiempo_vuelo_simulado = latencia_base / FACTOR_ACELERACION

        transmitidos = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drenaje ordenado: Prioridad 1 primero, luego 2, luego 3; y por antigüedad
            cursor.execute("""
                SELECT id, prioridad, tipo_evento, payload, creado 
                FROM cola_tierra 
                WHERE estado_envio = 'retenido' 
                ORDER BY prioridad ASC, creado ASC
            """)
            mensajes = cursor.fetchall()
            
            now = datetime.utcnow()
            llegada = now + timedelta(seconds=tiempo_vuelo_simulado)
            
            for msg in mensajes:
                cursor.execute("""
                    UPDATE cola_tierra 
                    SET estado_envio = 'en_transito',
                        transmitido = ?,
                        llegada_estimada = ?
                    WHERE id = ?
                """, (now.isoformat(), llegada.isoformat(), msg["id"]))
                
                transmitidos.append(dict(msg))
                
            conn.commit()
        return transmitidos
```

### 3. Rutas y Controladores API (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sqlite3
from engine import evaluar_news2, evaluar_ambiente
from queue_manager import QueueManager

app = FastAPI(title="ORBIT Health Local Clinical Engine", version="3.0")
qm = QueueManager()

class LecturaInput(BaseModel):
    astronauta_id: str
    indicador: str
    valor: float
    unidad: str
    signos_completos: Optional[Dict[str, Any]] = None

class DiarioInput(BaseModel):
    astronauta_id: str
    titulo: Optional[str] = "Nota Personal"
    contenido: str

class EstadoEnlaceInput(BaseModel):
    enlace_activo: bool
    entorno: str = "marte"

@app.post("/lecturas")
def registrar_lectura(datos: LecturaInput):
    # Evaluar riesgo clínico
    if datos.signos_completos:
        puntos_news, nivel = evaluar_news2(datos.signos_completos)
    else:
        # Evaluación de parámetro aislado
        puntos_news = 0
        nivel = "verde"
        if datos.indicador == "temperatura" and datos.valor >= 39.1:
            nivel = "amarillo"
            puntos_news = 2
        elif datos.indicador == "spo2" and datos.valor <= 91:
            nivel = "rojo"
            puntos_news = 3

    # Asignar prioridad en cola
    prioridad_map = {"rojo": 1, "amarillo": 2, "verde": 3}
    prioridad = prioridad_map[nivel]

    conn = sqlite3.connect("orbit_health.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lecturas (astronauta_id, indicador, valor, unidad, nivel_alerta, puntuacion_news2, origen)
        VALUES (?, ?, ?, ?, ?, ?, 'manual')
    """, (datos.astronauta_id, datos.indicador, datos.valor, datos.unidad, nivel, puntos_news))
    lectura_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Encolar para transmisión hacia la Tierra
    evento_id = qm.encolar_evento(
        astronauta_id=datos.astronauta_id,
        tipo_evento=f"LECTURA_{datos.indicador.upper()}",
        prioridad=prioridad,
        payload={"lectura_id": lectura_id, "valor": datos.valor, "alerta": nivel, "news2": puntos_news}
    )

    return {
        "status": "success",
        "lectura_id": lectura_id,
        "nivel_alerta": nivel,
        "puntuacion_news2": puntos_news,
        "cola_evento_id": evento_id
    }

@app.post("/diario")
def guardar_diario_privado(nota: DiarioInput):
    """
    Guarda notas personales en almacenamiento local sin enviar a la cola exterior.
    """
    conn = sqlite3.connect("orbit_health.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO diario_privado (astronauta_id, titulo, contenido)
        VALUES (?, ?, ?)
    """, (nota.astronauta_id, nota.titulo, nota.contenido))
    diario_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"status": "success", "diario_id": diario_id, "privado": True, "transmitido_tierra": False}

@app.post("/simulacion/sincronizar")
def sincronizar_cola(estado: EstadoEnlaceInput):
    despachados = qm.procesar_despacho(enlace_activo=estado.enlace_activo, entorno=estado.entorno)
    return {
        "enlace_activo": estado.enlace_activo,
        "entorno": estado.entorno,
        "mensajes_transmitidos": len(despachados),
        "items": despachados
    }
```

--------------------------------------------------------------------------------

## 6. Especificación de Componentes Frontend (React / TypeScript)

El frontend se organiza sin alterar la estructura validada en las pruebas anteriores, optimizando los renders mediante componentes puros:

### 1. `FiguraHumana.tsx` (Mapa Anatómico SVG Interactivo)
* **Objetivo:** Mostrar de un vistazo el estado clínico del tripulante sin sobrecargar el navegador.
* **Técnica:** Nodos SVG vectoriales nativos para las cinco zonas corporales: Cabeza/SNC, Sistema Cardiovascular, Sistema Respiratorio, Tronco/Metabólico, y Extremidades/Locomoción.
* **Optimización:** Implementación envuelta en `React.memo` para evitar renderizados redundantes al llegar mensajes por WebSocket o telemetría de fondo. Se suprimen filtros pesados de SVG (`filter="url(#drop-shadow)"`) reemplazándolos por transiciones CSS nativas en la propiedad `fill` y animación de opacidad con `@keyframes` para indicar alertas rojas o amarillas.

### 2. `PanelMedicion.tsx` (Formulario de Captura Manual Universal)
* Permite al tripulante o médico de a bordo ingresar valores directos cuando no se dispone de biosensores automáticos.
* Campos tipados:
  * Selector de astronauta.
  * Selector de variable fisiológica: Temperatura ($^\circ\text{C}$), Presión Sistólica (mmHg), Presión Diastólica (mmHg), Frecuencia Cardíaca (lpm), $\text{SpO}_2$ ($\%$), Glucosa capilar (mg/dL), Radiación acumulada (mSv).
  * Validación reactiva de rango numérico fisiológico antes del envío a `POST /lecturas`.

### 3. `DiarioTripulante.tsx` (Registro de Bienestar Conductual)
* Área de texto libre para notas reflexivas.
* Presenta una etiqueta visual prominente: *"Almacenamiento Local Seguro — Desconectado de Telemetría Externa"*.
* Persiste hacia `POST /diario`, confirmando en pantalla que la información permanece bajo custodia del tripulante.

### 4. `ConsolaTierra.tsx` (Monitor del Enlace Orbital y Modo Eclipse)
* Panel interactivo para conmutar entre:
  * Entorno: Luna ($1.3\text{ s}$) / Marte ($1200\text{ s}$).
  * Estado del canal: Normal / Modo Eclipse (conjunción solar o fallo de antena).
* Gráfico de la cola de retransmisión que visualiza los mensajes retenidos, agrupados por su nivel de prioridad (rojo, amarillo, verde), permitiendo observar cómo al desactivar el Modo Eclipse los eventos críticos salen con preferencia inmediata.

--------------------------------------------------------------------------------

## 7. Pipeline de Verificación, Pruebas y Despliegue

Para certificar que la solución es sólida y auditable, se establecen tres fases de aseguramiento de calidad antes de la presentación:

### 1. Ejecución de Pruebas Unitarias y de Integración (`pytest`)
La suite existente de cincuenta y nueve pruebas debe mantenerse en verde. Se agregan pruebas automatizadas para la prioridad de la cola y las reglas ambientales:

```bash
# Ejecutar suite de pruebas con detalle de cobertura
pytest tests/ -v --tb=short
```

Pruebas específicas a validar:
* `test_news2_severo_alerta_roja`: Comprueba que una frecuencia respiratoria $\ge 25$ o saturación $\le 91\%$ compute alerta roja y prioridad 1.
* `test_diario_privado_no_encolado`: Verifica mediante consulta SQL que ninguna entrada en `diario_privado` genere filas en `cola_tierra`.
* `test_cola_prioridad_eclipse`: Inserta eventos verdes, amarillos y rojos en Modo Eclipse; ejecuta la reconexión y verifica que el primer mensaje despachado sea el de prioridad 1.

### 2. Compilación de Producción Libre de Dependencias Externas
No se debe presentar la plataforma en modo de desarrollo (`npm run dev`). La aplicación debe empaquetarse para optimizar memoria y tiempos de carga:

```bash
# Compilación estática de producción en React
npm run build
```

El servidor web sirve los archivos estáticos generados desde la carpeta `dist/` o `build/`, garantizando una carga inicial inferior a dos segundos y una respuesta al clic menor a cien milisegundos.

### 3. Prueba de Fuego: Validación Offline E2E (*Wi-Fi Off Test*)
Antes de la grabación del vídeo o sustentación en vivo:
1. Desconectar la interfaz inalámbrica de red y desconectar cualquier cable Ethernet del equipo.
2. Iniciar el servidor local y abrir el navegador en `http://localhost:3000`.
3. Navegar por todas las vistas, realizar un registro manual de signos vitales, alternar al Modo Eclipse, escribir en el diario privado y simular el restablecimiento del enlace.
4. La ausencia de errores de red o advertencias de librerías faltantes demuestra formalmente la autonomía técnica exigida para el espacio profundo.

--------------------------------------------------------------------------------

## 8. Guion de Demostración para el Pitch ante el Jurado (3 Minutos)

Una presentación exitosa debe demostrar competencia técnica, honestidad metodológica y alineación con los estándares espaciales:

* **0:00 – 0:40 | El Reto de Marte:**  
  *"En una misión interplanetaria a 140 millones de millas, la distancia impone un retardo de comunicaciones de hasta 20 minutos por sentido, y los campos gravitatorios variables causan pérdida de densidad ósea de hasta 1.5% al mes. La tripulación no puede contar con telemedicina en tiempo real ni misiones de rescate. Presentamos ORBIT Health, una plataforma de apoyo a la decisión clínica diseñada para operar en autonomía absoluta bajo comunicaciones degradadas."*

* **0:40 – 1:30 | Rigor Metodológico y Datos:**  
  *"Al no existir telemetría médica pública en espacio profundo, hemos validado nuestro sistema integrando series fisiológicas reales de PhysioNet en una base de datos local SQLite. En lugar de modelos de caja negra no auditables, implementamos un motor determinista basado en NEWS2 del Royal College of Physicians y el tamizaje anímico PHQ-2, adaptando umbrales para correlacionar signos vitales con la acumulación de dióxido de carbono en la cabina y la radiación espacial."*

* **1:30 – 2:20 | Demostración en Vivo (Totalmente Offline):**  
  *(Operando con el Wi-Fi apagado)*  
  *"Aquí observan que el sistema responde instantáneamente sin internet. Registramos un cuadro de hipoxia aguda en nuestro panel manual: la figura anatómica refleja la alerta de inmediato. Ahora activamos el Modo Eclipse: la nave pierde contacto con la Tierra. Registramos mediciones rutinarias y un segundo evento crítico. Como pueden ver en la consola, la cola local retiene los paquetes con un hash criptográfico encadenado. Al restaurar el enlace orbital, nuestro algoritmo de prioridad transmite inmediatamente la emergencia roja hacia la Tierra antes que la telemetría secundaria."*

* **2:20 – 3:00 | Humanidad y Conclusión:**  
  *"Además, protegiendo la salud conductual según las pautas de la NASA, incluimos un módulo de diario personal completamente aislado de la telemetría exterior, garantizando un espacio seguro para el astronauta. ORBIT Health combina rigor clínico, tolerancia a fallos y autosuficiencia para proteger a los pioneros que nos llevarán a Marte."*
