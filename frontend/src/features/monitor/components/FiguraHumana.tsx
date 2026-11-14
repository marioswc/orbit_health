import { useTranslation } from "../../../i18n";
import { nivelActual } from "../../../shared/rendimiento";
import { memo, useEffect, useMemo, useRef, type CSSProperties, type KeyboardEvent, type PointerEvent } from "react";
import type { LecturaEstado } from "../types/estado";
import { ETIQUETAS, anguloFlecha, origenEtiqueta } from "../etiquetas";
import { ZONAS, ancla, nivelZona, type Capa, type NivelZona } from "../zonas";
import { ZONA_PATHS } from "../zonasPaths";
import { CAPAS_ANAT, Capas, VB, VIEWBOX, precargar } from "./ArteAstronauta";

interface Props {
  lecturas: LecturaEstado[];
  seleccionada: string;
  acercado: boolean;
  capa: Capa;
  /** Meses en microgravedad (0-6): el hueso se ve menos denso (metafora visual). */
  meses: number;
  alSeleccionar: (id: string) => void;
  alAlejar: () => void;
  /** Peor nivel del aire/radiacion de cabina (lo informa el backend). Si es amarillo o rojo, marca Cabeza y Respiratorio. */
  ambiente?: NivelZona | null;
}

// Orden de dibujo: lo pequeno encima de lo grande para que reciba el clic
const ORDEN_HIT = ["piernas", "brazos", "metab", "cardio", "resp", "snc"];
const CENTRO = { x: 237, y: 236 }; // hacia donde se lleva la zona al acercar la camara

/** Estilo de la camara en CSS (porcentajes del lienzo): acerca con escala desde el punto y lo centra. */
export function estiloCamara(zonaId: string, capa: Capa, acercado: boolean): CSSProperties {
  const z = ZONAS.find((x) => x.id === zonaId);
  if (!acercado || !z) return { transformOrigin: "50% 50%", transform: "none" };
  const [ax, ay] = ancla(z, capa);
  const pctX = (v: number) => ((v - VB.x) / VB.w) * 100;
  const pctY = (v: number) => ((v - VB.y) / VB.h) * 100;
  return {
    transformOrigin: `${pctX(ax)}% ${pctY(ay)}%`,
    transform: `translate(${((CENTRO.x - ax) / VB.w) * 100}%, ${((CENTRO.y - ay) / VB.h) * 100}%) scale(${z.zoom})`,
  };
}

const ZONAS_AMBIENTE = ["snc", "resp"]; // el CO2 y la radiacion afectan sobre todo al SNC y al sistema respiratorio

function FiguraHumana({ lecturas, seleccionada, acercado, capa, meses, alSeleccionar, alAlejar, ambiente = null }: Props) {
  const { t } = useTranslation("monitor");
  const plataforma = useRef<HTMLDivElement>(null);
  const visitadas = useRef<Set<Capa>>(new Set(["traje"]));
  visitadas.current.add(capa);

  // Descarga las capas de anatomia cuando el navegador esta libre (no bloquea la primera carga)
  useEffect(() => {
    if (nivelActual() === "bajo") return; // equipos modestos: las capas se bajan solo al elegirlas
    const idle = window.requestIdleCallback ?? ((f: () => void) => window.setTimeout(f, 1500));
    const id = idle(() => CAPAS_ANAT.forEach(precargar));
    return () => { if (window.cancelIdleCallback) window.cancelIdleCallback(id as number); else window.clearTimeout(id as number); };
  }, []);

  const zona = ZONAS.find((z) => z.id === seleccionada);
  const s = acercado && zona ? zona.zoom : 1;
  const niveles = useMemo(() => Object.fromEntries(ZONAS.map((z) => [z.id, nivelZona(z.indicadores, lecturas)])), [lecturas]);

  // Inclinacion suave con el cursor: una sola actualizacion por fotograma, sin re-render
  const pendiente = useRef<{ x: number; y: number } | null>(null);
  const cuadro = useRef(0);
  function mover(e: PointerEvent<HTMLDivElement>) {
    if (e.pointerType !== "mouse") return;
    const r = e.currentTarget.getBoundingClientRect();
    pendiente.current = { x: (e.clientX - r.left) / r.width - 0.5, y: (e.clientY - r.top) / r.height - 0.5 };
    if (cuadro.current) return;
    cuadro.current = requestAnimationFrame(() => {
      cuadro.current = 0;
      const p = pendiente.current;
      if (p && plataforma.current) {
        plataforma.current.style.setProperty("--rx", p.x.toFixed(3));
        plataforma.current.style.setProperty("--ry", p.y.toFixed(3));
      }
    });
  }
  function soltar() { plataforma.current?.style.setProperty("--rx", "0"); plataforma.current?.style.setProperty("--ry", "0"); }
  useEffect(() => () => { if (cuadro.current) cancelAnimationFrame(cuadro.current); }, []);

  const ambienteDe = (id: string) => (ZONAS_AMBIENTE.includes(id) && (ambiente === "amarillo" || ambiente === "rojo") ? ambiente : null);

  const propsZona = (id: string) => {
    const z = ZONAS.find((x) => x.id === id)!;
    const n = niveles[id];
    const amb = ambienteDe(id);
    return {
      className: `zona ${n}`, role: "button", tabIndex: 0, "aria-pressed": seleccionada === id,
      "aria-label": amb
        ? t("figura.zonaAriaAmb", { zona: t(`zona.${id}.etiqueta`), estado: t(`common:status.${n}`), amb: t(`common:status.${amb}`) })
        : t("figura.zonaAria", { zona: t(`zona.${id}.etiqueta`), estado: t(`common:status.${n}`) }),
      onClick: () => alSeleccionar(id),
      onKeyDown: (e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alSeleccionar(id); } },
    };
  };

  const etiquetas = (ETIQUETAS[capa] ?? []).filter((e) => !acercado || e.zona === seleccionada);

  return (
    <div className={`plataforma${capa !== "traje" ? " capa-anat" : ""}`} ref={plataforma} onPointerMove={mover} onPointerLeave={soltar}>
      <span key={`barrido-${seleccionada}-${capa}`} className="barrido" aria-hidden="true" />
      <i className="esquina e1" aria-hidden="true" /><i className="esquina e2" aria-hidden="true" />
      <i className="esquina e3" aria-hidden="true" /><i className="esquina e4" aria-hidden="true" />
      <span className="hud-capa" aria-hidden="true">{t(`capa.${capa}`)}</span>

      <div className="inclina">
        <div className="lienzo" role="group" aria-label={t("figura.grupoAria")}>
          <div className="camara" style={estiloCamara(seleccionada, capa, acercado)}>
            <Capas capa={capa} meses={meses} zona={seleccionada} enfocar={acercado} visitadas={visitadas.current} />

            <svg className="overlay" viewBox={VIEWBOX} preserveAspectRatio="none">
              <g className="zonas">
                {ORDEN_HIT.map((id) => <g key={id} {...propsZona(id)}><title>{t(`zona.${id}.etiqueta`)}</title><path d={ZONA_PATHS[id]} /></g>)}
              </g>

              {/* flechas que senalan los organos / musculos / huesos de la capa visible */}
              <g className="flechas" pointerEvents="none">
                {etiquetas.map((e) => {
                  const [ox, oy] = origenEtiqueta(e, acercado);
                  return (
                    <g key={`${capa}-${e.texto}-${acercado}`} className="flecha">
                      <line className="flecha-linea" x1={ox} y1={oy} x2={e.tx} y2={e.ty} />
                      <g transform={`translate(${e.tx} ${e.ty}) rotate(${anguloFlecha(e, acercado)}) scale(${1 / s})`}>
                        <path className="flecha-punta" d="M0 0 L-5.5 -2.6 L-5.5 2.6 Z" />
                      </g>
                      <g transform={`translate(${ox} ${oy}) scale(${1 / s})`}>
                        <text className="flecha-texto" x={e.lado === "izq" ? -3 : 3} y={1.8} textAnchor={e.lado === "izq" ? "end" : "start"}>{t(`etiqueta.${e.texto}`)}</text>
                      </g>
                    </g>
                  );
                })}
              </g>

              <g className="puntos">
                {ZONAS.map((z) => {
                  const [ax, ay] = ancla(z, capa);
                  const amb = ambienteDe(z.id);
                  return (
                    <g key={z.id} transform={`translate(${ax} ${ay})`}>
                      <g className={`punto ${niveles[z.id]} ${seleccionada === z.id ? "sel" : ""}${amb ? ` amb-${amb}` : ""}`} style={{ transform: `scale(${1 / s})` }} aria-hidden="true" pointerEvents="none">
                        {amb && <circle className="p-ambiente" r="8.5" />}
                        <circle className="p-anillo" r="5" />
                        <circle className="p-base" r="4" />
                        <circle className="p-centro" r="1.5" />
                      </g>
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>
        </div>
      </div>
      {acercado && <button type="button" className="ver-todo" onClick={alAlejar}>{t("figura.verTodo")}</button>}
    </div>
  );
}

export default memo(FiguraHumana);
