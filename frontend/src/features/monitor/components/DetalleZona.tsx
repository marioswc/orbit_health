import type { LecturaEstado } from "../types/estado";
import { CAPAS, FUENTE_EFECTOS, ZONAS, nivelZona, type Capa } from "../zonas";

import { MESES_MAX, textoPerdida } from "../utils/perdidaOsea";

interface Props {
  id: string;
  lecturas: LecturaEstado[];
  capa: Capa;
  meses: number;
  alMeses: (m: number) => void;
}

export default function DetalleZona({ id, lecturas, capa, meses, alMeses }: Props) {
  const zona = ZONAS.find((z) => z.id === id);
  if (!zona) return null;
  const nivel = nivelZona(zona.indicadores, lecturas);
  const dentro = lecturas.filter((l) => zona.indicadores.includes(l.indicador));
  const textoCapa = zona.anatomia[capa];
  const huesoDeCarga = capa === "hueso" && (zona.id === "brazos" || zona.id === "piernas");

  return (
    // key: al cambiar de zona se reinicia la animacion de entrada
    <section key={zona.id} className="detalle" aria-live="polite">
      <h2>{zona.etiqueta}</h2>
      <span className={`badge ${nivel}`}>{nivel === "sin_datos" ? "sin datos" : nivel}</span>

      {capa !== "traje" && (
        <div className="capa-info" key={capa}>
          <h3>Capa: {CAPAS.find((c) => c.id === capa)?.etiqueta}</h3>
          <p>{textoCapa ?? "Esta capa no tiene información específica para esta zona en las fuentes del proyecto."}</p>
          {huesoDeCarga && (
            <div className="osea">
              <label htmlFor="meses-mg">Tiempo en microgravedad: <strong>{meses} {meses === 1 ? "mes" : "meses"}</strong></label>
              <input id="meses-mg" type="range" min={0} max={MESES_MAX} step={1} value={meses} onChange={(e) => alMeses(Number(e.target.value))} />
              <p className="osea-dato">
                Pérdida de densidad ósea estimada: <strong>{textoPerdida(meses)}</strong>
              </p>
              <p className="fuente">Cálculo simple del equipo con una tasa constante de ≈1–1.5 % por mes (NASA HRP). Es ilustrativo, no una predicción individual; los puntos del dibujo son solo una metáfora visual.</p>
            </div>
          )}
        </div>
      )}

      <h3>Indicadores</h3>
      {zona.indicadores.length === 0 && <p className="suave">Esta zona no tiene indicadores en el prototipo.</p>}
      {zona.indicadores.length > 0 && dentro.length === 0 && <p className="suave">Sin lecturas recientes de: {zona.indicadores.join(", ")}.</p>}
      {dentro.map((l) => (
        <div key={l.indicador} className="item">
          <span>{l.indicador}</span>
          <span className="valor"><span>{l.valor} {l.unidad}</span><span className={`badge ${l.nivel}`}>{l.nivel}</span></span>
        </div>
      ))}

      <h3>Qué puede dañar el vuelo espacial aquí: {zona.peligro}</h3>
      <ul className="efectos">
        {zona.efectos.map((e, i) => <li key={e} style={{ ["--i" as string]: i }}>{e}</li>)}
      </ul>
      <p className="fuente">Fuente: {FUENTE_EFECTOS}. Efectos generales de la misión, no un diagnóstico del tripulante.</p>
    </section>
  );
}
