import { memo } from "react";
import type { LecturaEstado } from "../types/estado";
import { nombreIndicador } from "../utils/indicadores";
import { compararConBase, formatoDelta } from "../utils/lineaBase";

interface Props {
  lectura: LecturaEstado;
  /** Destella al cambiar el valor (se usa tras la primera carga). */
  destello?: boolean;
}

/** Signo vital con su valor actual y la comparacion contra la linea base personal. */
function TarjetaSignoVital({ lectura: l, destello = false }: Props) {
  const c = compararConBase(l);
  const nombre = nombreIndicador(l.indicador);
  const fueraDeRango = l.nivel !== "verde";
  const normal = !fueraDeRango && !c.desvio;

  return (
    <article className={`signo ${l.nivel}${destello ? " destello" : ""}`} aria-label={`${nombre}: ${l.valor} ${l.unidad}, ${l.nivel}`}>
      <header className="signo-cab">
        <span className="signo-nombre">{nombre}</span>
        <span className={`badge ${l.nivel}`}>{l.nivel}</span>
      </header>
      <p className="signo-valor"><strong>{l.valor}</strong> <span>{l.unidad}</span></p>
      {c.disponible && c.media !== undefined && c.delta !== undefined ? (
        <p className="signo-base">Tu línea base: {Number(c.media.toFixed(1))} {l.unidad} ({formatoDelta(c.delta)})</p>
      ) : (
        <p className="signo-base suave">Sin línea base suficiente ({c.muestras} {c.muestras === 1 ? "lectura" : "lecturas"})</p>
      )}
      <p className="signo-estado">
        <span className="tendencia" aria-hidden="true">{c.tendencia}</span>
        {normal && <span className="etiqueta-estado">Normal</span>}
        {fueraDeRango && <span className="etiqueta-estado alerta">Fuera de rango</span>}
        {c.desvio && <span className="etiqueta-estado desvio">Desvío &gt; 2σ</span>}
      </p>
    </article>
  );
}

export default memo(TarjetaSignoVital);

