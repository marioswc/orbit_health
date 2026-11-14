import { memo } from "react";
import type { AlertaColectiva } from "../types/cabina";
import { DESCRIPCION_CO2, type Ambiente } from "../utils/ambiente";

interface Props {
  ambiente: Ambiente;
  alerta: AlertaColectiva | null;
}

/** Aire (CO2) y radiacion acumulada de la cabina, con la alerta colectiva cuando aplica. */
function MonitorCabina({ ambiente, alerta }: Props) {
  const { co2, co2Nivel, dosis } = ambiente;
  const pct = dosis ? Math.min(100, Math.max(0, dosis.valor)) : 0;

  return (
    <div className="panel cabina" role="region" aria-label="Monitor de cabina">
      <h2>Cabina</h2>

      <div className="cabina-dato">
        <span className="cabina-rotulo">CO₂ en cabina</span>
        {co2 !== null ? (
          <>
            <p className="cabina-valor"><strong>{co2}</strong> <span>mmHg</span></p>
            {co2Nivel ? (
              <p className="cabina-estado"><span className={`badge ${co2Nivel}`}>{co2Nivel}</span><span className="suave">{DESCRIPCION_CO2[co2Nivel]}</span></p>
            ) : (
              <p className="suave">El backend no informó el nivel de esta lectura.</p>
            )}
          </>
        ) : (
          <p className="suave">Sin lectura reciente de CO₂.</p>
        )}
      </div>

      <div className="cabina-dato">
        <span className="cabina-rotulo">Dosis acumulada</span>
        {dosis ? (
          <>
            <p className="cabina-valor"><strong>{dosis.valor}</strong> <span>% del límite de misión</span></p>
            <div className="medidor" role="progressbar" aria-label="Dosis acumulada de radiación" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
              <span className={`medidor-relleno ${dosis.nivel}`} style={{ transform: `scaleX(${pct / 100})` }} />
            </div>
            <p className="cabina-estado"><span className={`badge ${dosis.nivel}`}>{dosis.nivel}</span></p>
          </>
        ) : (
          <p className="suave">Sin lectura reciente de dosis.</p>
        )}
      </div>

      {alerta && (
        <div className="cabina-alerta" role="alert">
          <span className={`badge ${alerta.nivel}`}>{alerta.nivel}</span>
          <strong>{alerta.nombre}</strong>
          <p>{alerta.afectados} {alerta.afectados === 1 ? "tripulante afectado" : "tripulantes afectados"} · CO₂ {alerta.co2_mmhg} mmHg</p>
        </div>
      )}

      <p className="fuente">Umbrales: supuestos de diseño, pendientes de validación médica.</p>
    </div>
  );
}

export default memo(MonitorCabina);

