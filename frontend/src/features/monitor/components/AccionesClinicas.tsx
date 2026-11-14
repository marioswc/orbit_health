import { memo } from "react";
import Alerta from "../../../shared/components/Alerta";
import type { Nivel } from "../../../shared/types/nivel";
import type { ReglaCombinada } from "../types/estado";

interface Props {
  nivel: Nivel | "sin_datos";
  proximaCapturaMin?: number;
  reglas?: ReglaCombinada[];
  acciones?: string[];
}

const TONO: Record<Nivel, "ok" | "aviso" | "error"> = { verde: "ok", amarillo: "aviso", rojo: "error" };

/** Reglas combinadas activas y pasos procedimentales sugeridos por el backend. */
function AccionesClinicas({ nivel, proximaCapturaMin, reglas = [], acciones = [] }: Props) {
  if (reglas.length === 0 && acciones.length === 0 && proximaCapturaMin === undefined) return null;

  return (
    <section className="tarjeta acciones-clinicas" aria-label="Acciones y reglas activas">
      <div className="acciones-cab">
        <h2>Acciones sugeridas</h2>
        {proximaCapturaMin !== undefined && (
          <span className="captura-rec">Repetir medición cada {proximaCapturaMin} min</span>
        )}
      </div>

      {reglas.length > 0 && (
        <div className="reglas-activas" role="list" aria-label="Reglas combinadas activas">
          {reglas.map((r) => (
            <div key={r.id} role="listitem">
              <Alerta tono={TONO[r.nivel]} titulo={r.nombre}>
                Cruce de señales detectado · nivel {r.nivel} (supuesto de diseño).
              </Alerta>
            </div>
          ))}
        </div>
      )}

      {acciones.length > 0 && (
        <ul className="acciones-lista">
          {acciones.map((a) => <li key={a}>{a}</li>)}
        </ul>
      )}
    </section>
  );
}

export default memo(AccionesClinicas);
