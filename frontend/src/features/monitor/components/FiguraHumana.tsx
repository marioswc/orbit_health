import { memo, useRef, type KeyboardEvent, type PointerEvent } from "react";
import type { LecturaEstado } from "../types/estado";
import { CAPAS, ZONAS, ancla, nivelZona, type Capa } from "../zonas";
import { ZONA_PATHS } from "../zonasPaths";
import { Capas, VIEWBOX } from "./ArteAstronauta";

interface Props {
  lecturas: LecturaEstado[];
  seleccionada: string;
  acercado: boolean;
  capa: Capa;
  /** Meses en microgravedad (0-6): el hueso se ve menos denso (metafora visual). */
  meses: number;
  alSeleccionar: (id: string) => void;
  alAlejar: () => void;
}

// Orden de dibujo: lo pequeno encima de lo grande para que reciba el clic
const ORDEN_HIT = ["piernas", "brazos", "metab", "cardio", "resp", "snc"];
const CENTRO = { x: 237, y: 236 };
const CENTRO_PAR: [number, number] = [237, 236]; // hacia donde se lleva la zona al acercar la camara

function FiguraHumana({ lecturas, seleccionada, acercado, capa, meses, alSeleccionar, alAlejar }: Props) {
  const plataforma = useRef<HTMLDivElement>(null);
  const zona = ZONAS.find((z) => z.id === seleccionada);
  const s = acercado && zona ? zona.zoom : 1;
  const az = zona ? ancla(zona, capa) : CENTRO_PAR;
  const camara = acercado && zona
    ? { transformOrigin: `${az[0]}px ${az[1]}px`, transform: `translate(${CENTRO.x - az[0]}px, ${CENTRO.y - az[1]}px) scale(${s})` }
    : { transformOrigin: `${CENTRO.x}px ${CENTRO.y}px`, transform: "none" };

  // Inclinacion suave con el cursor (variables CSS, sin re-render)
  function mover(e: PointerEvent<HTMLDivElement>) {
    if (e.pointerType !== "mouse" || !plataforma.current) return;
    const r = e.currentTarget.getBoundingClientRect();
    plataforma.current.style.setProperty("--rx", ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
    plataforma.current.style.setProperty("--ry", ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
  }
  function soltar() { plataforma.current?.style.setProperty("--rx", "0"); plataforma.current?.style.setProperty("--ry", "0"); }

  const propsZona = (id: string) => {
    const z = ZONAS.find((x) => x.id === id)!;
    const n = nivelZona(z.indicadores, lecturas);
    return {
      className: `zona ${n}`, role: "button", tabIndex: 0, "aria-pressed": seleccionada === id,
      "aria-label": `${z.etiqueta}: ${n === "sin_datos" ? "sin datos" : n}`,
      onClick: () => alSeleccionar(id),
      onKeyDown: (e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alSeleccionar(id); } },
    };
  };

  return (
    <div className={`plataforma${capa !== "traje" ? " capa-anat" : ""}`} ref={plataforma} onPointerMove={mover} onPointerLeave={soltar}>
      <span key={`barrido-${seleccionada}-${capa}`} className="barrido" aria-hidden="true" />
      <i className="esquina e1" aria-hidden="true" /><i className="esquina e2" aria-hidden="true" />
      <i className="esquina e3" aria-hidden="true" /><i className="esquina e4" aria-hidden="true" />
      <span className="hud-capa" aria-hidden="true">{CAPAS.find((c) => c.id === capa)?.etiqueta}</span>

      <div className="inclina">
        <svg className="figura" viewBox={VIEWBOX} role="group" aria-label="Astronauta de frente: mapa de estado clínico por zona">
          <g className="camara" style={camara}>
            <Capas capa={capa} meses={meses} zona={seleccionada} />

            <g className="zonas">
              {ORDEN_HIT.map((id) => <g key={id} {...propsZona(id)}><title>{ZONAS.find((z) => z.id === id)!.etiqueta}</title><path d={ZONA_PATHS[id]} /></g>)}
            </g>

            {acercado && zona && <line key={`ll-${zona.id}`} className="llamada" x1={az[0]} y1={az[1]} x2={az[0] + 300} y2={az[1]} style={{ strokeWidth: 0.7 / s }} />}

            <g className="puntos">
              {ZONAS.map((z) => {
                const n = nivelZona(z.indicadores, lecturas);
                const an = ancla(z, capa);
                return (
                  <g key={z.id} transform={`translate(${an[0]} ${an[1]})`}>
                    <g className={`punto ${n} ${seleccionada === z.id ? "sel" : ""}`} style={{ transform: `scale(${1 / s})` }} aria-hidden="true" pointerEvents="none">
                      <circle className="p-anillo" r="5" />
                      <circle className="p-base" r="4" />
                      <circle className="p-centro" r="1.5" />
                    </g>
                  </g>
                );
              })}
            </g>
          </g>
        </svg>
      </div>
      {acercado && <button type="button" className="ver-todo" onClick={alAlejar}>Ver cuerpo completo</button>}
    </div>
  );
}

export default memo(FiguraHumana);
