import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { LecturaEstado } from "../types/estado";
import { nombreIndicador } from "../utils/nombreIndicador";

const ORDEN = { rojo: 0, amarillo: 1, verde: 2, sin_datos: 3 } as const;
const TEXTO = { rojo: "rojo", amarillo: "amarillo", verde: "verde", sin_datos: "sin datos" } as const;
const UMBRAL_VER_TODOS = 5;

interface Props {
  lecturas: LecturaEstado[];
  /** Tras la primera carga, los datos que cambian destellan. */
  destellar: boolean;
  alAbrirCaptura?: () => void;
}

const FLECHA = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

/**
 * Indicadores en una sola fila desplazable (los graves primero) que no crece con el numero de lecturas.
 * "Ver todos" despliega una rejilla con scroll interno acotado.
 */
export default function TiraIndicadores({ lecturas, destellar, alAbrirCaptura }: Props) {
  const [abierta, setAbierta] = useState(false);
  const [borde, setBorde] = useState({ ini: false, fin: false });
  const pista = useRef<HTMLDivElement>(null);

  const ordenadas = useMemo(
    () => [...lecturas].sort((a, b) => ORDEN[a.nivel] - ORDEN[b.nivel] || nombreIndicador(a.indicador).localeCompare(nombreIndicador(b.indicador), "es")),
    [lecturas],
  );
  const conteo = useMemo(() => {
    const c = { rojo: 0, amarillo: 0, verde: 0, sin_datos: 0 };
    for (const l of lecturas) c[l.nivel] += 1;
    return c;
  }, [lecturas]);

  const medir = useCallback(() => {
    const el = pista.current;
    if (!el) return;
    setBorde({ ini: el.scrollLeft > 2, fin: el.scrollLeft + el.clientWidth < el.scrollWidth - 2 });
  }, []);
  useEffect(() => {
    medir();
    window.addEventListener("resize", medir);
    return () => window.removeEventListener("resize", medir);
  }, [medir, ordenadas, abierta]);

  const mover = (dir: 1 | -1) => pista.current?.scrollBy({ left: dir * Math.max(240, pista.current.clientWidth * 0.7), behavior: "smooth" });

  if (lecturas.length === 0) {
    return (
      <section className="indicadores" aria-label="Indicadores">
        <p className="tira-vacia suave">
          Sin lecturas recientes.{" "}
          {alAbrirCaptura && <button type="button" className="enlace" onClick={alAbrirCaptura}>Registrar una medición</button>}
        </p>
      </section>
    );
  }

  const puedeDesplazar = !abierta && (borde.ini || borde.fin);
  return (
    <section className="indicadores" aria-label="Indicadores">
      <header className="ind-cab">
        <h2>Indicadores <span className="ind-total">{lecturas.length}</span></h2>
        <ul className="ind-resumen" aria-label="Resumen por estado">
          {(Object.keys(ORDEN) as (keyof typeof ORDEN)[]).filter((k) => conteo[k] > 0).map((k) => (
            <li key={k}><span className={`badge ${k}`}>{conteo[k]} {TEXTO[k]}</span></li>
          ))}
        </ul>
        <div className="ind-acciones">
          {puedeDesplazar && (
            <>
              <button type="button" className="ghost icono" onClick={() => mover(-1)} disabled={!borde.ini} aria-label="Indicadores anteriores"><svg {...FLECHA}><path d="m15 6-6 6 6 6" /></svg></button>
              <button type="button" className="ghost icono" onClick={() => mover(1)} disabled={!borde.fin} aria-label="Indicadores siguientes"><svg {...FLECHA}><path d="m9 6 6 6-6 6" /></svg></button>
            </>
          )}
          {lecturas.length > UMBRAL_VER_TODOS && (
            <button type="button" onClick={() => setAbierta((a) => !a)} aria-expanded={abierta}>{abierta ? "Ver menos" : `Ver todos (${lecturas.length})`}</button>
          )}
        </div>
      </header>
      <div
        ref={pista} onScroll={medir}
        className={`tira${abierta ? " abierta" : ""}${!abierta && borde.ini ? " fade-ini" : ""}${!abierta && borde.fin ? " fade-fin" : ""}`}
        tabIndex={abierta ? undefined : 0} role="list"
      >
        {ordenadas.map((i) => (
          <div key={`${i.indicador}-${i.valor}-${i.ts}`} role="listitem" className={`chip-ind ${i.nivel}${destellar ? " destello" : ""}`}>
            <span className="chip-nombre" title={nombreIndicador(i.indicador)}>{nombreIndicador(i.indicador)}</span>
            <span className="chip-dato"><span>{i.valor}</span><small>{i.unidad}</small></span>
            <span className={`badge ${i.nivel}`}>{TEXTO[i.nivel]}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
