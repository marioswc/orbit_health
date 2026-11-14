import { useCallback, useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import { textoTipo } from "./ConsolaEnlace";

interface MensajeTierra {
  id: number;
  tripulante_id: string;
  tipo_evento: string;
  prioridad: number;
  transmitido_ts?: string;
}

interface RespuestaTierra {
  timestamp_tierra: string;
  recibidos: MensajeTierra[];
}

interface TripulanteInforme {
  id: string;
  nombre: string;
  rol: string;
  nivel_general: string;
  news2: { puntos: number; nivel: string };
}

interface InformeTripulacion {
  generado_ts: string;
  aviso: string;
  tripulacion: TripulanteInforme[];
}

const PRIO_NIVEL: Record<number, string> = { 1: "rojo", 2: "amarillo", 3: "verde" };

/** Vista de solo lectura del centro de control en Tierra e informe exportable. */
export default function VistaTierra() {
  const [tierra, setTierra] = useState<RespuestaTierra | null>(null);
  const [informe, setInforme] = useState<InformeTripulacion | null>(null);

  const cargar = useCallback(() => {
    api<RespuestaTierra>("/tierra/mensajes?limite=12").then(setTierra).catch(() => {});
    api<InformeTripulacion>("/informe").then(setInforme).catch(() => {});
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  return (
    <section className="tarjeta pieza tierra-bloque" aria-label="Vista de Tierra e informe">
      <div className="tierra-cab">
        <div>
          <h2>Centro de control en Tierra</h2>
          <p className="suave">Solo lo que ya llegó según la latencia actual, con lo urgente primero.</p>
        </div>
        <button type="button" className="ghost" onClick={cargar}>Actualizar</button>
      </div>

      {tierra && tierra.recibidos.length > 0 ? (
        <ul className="tierra-lista">
          {tierra.recibidos.slice(0, 8).map((m) => (
            <li key={m.id}>
              <span className={`badge ${PRIO_NIVEL[m.prioridad] ?? "sin_datos"}`}>P{m.prioridad}</span>
              <strong>{m.tripulante_id}</strong>
              <span>{textoTipo(m.tipo_evento)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="suave">Aún no han llegado eventos recibidos a Tierra.</p>
      )}

      {informe && (
        <div className="informe-bloque">
          <div className="tierra-cab">
            <div>
              <h3>Informe exportable para Tierra</h3>
              <p className="suave">{informe.aviso}</p>
            </div>
            <a className="ghost informe-btn" href="/api/informe" target="_blank" rel="noreferrer">
              Ver JSON
            </a>
          </div>
          <ul className="informe-lista">
            {informe.tripulacion.map((t) => (
              <li key={t.id}>
                <span>
                  <strong>{t.nombre}</strong> <span className="suave">({t.rol})</span>
                </span>
                <span className="informe-acciones">
                  <span className={`badge ${t.nivel_general}`}>{t.nivel_general}</span>
                  <a className="ghost informe-btn" href={`/api/informe/${encodeURIComponent(t.id)}?formato=csv`} download>
                    CSV {t.id}
                  </a>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

