import { useRef, type KeyboardEvent } from "react";

export interface OpcionSegmento { valor: string; etiqueta: string }

interface Props {
  opciones: OpcionSegmento[];
  /** "" = ninguna elegida. */
  valor: string;
  alCambiar: (valor: string) => void;
  etiqueta: string;
  /** Distribuye las opciones en una rejilla de 2 columnas (para textos largos). */
  rejilla?: boolean;
}

/** Control segmentado (radiogroup): una opcion a la vez, flechas para moverse, foco rotatorio. */
export default function Segmentado({ opciones, valor, alCambiar, etiqueta, rejilla = false }: Props) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const sel = opciones.findIndex((o) => o.valor === valor);

  function teclas(e: KeyboardEvent, i: number) {
    const sig = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
    if (!sig) return;
    e.preventDefault();
    const j = (i + sig + opciones.length) % opciones.length;
    alCambiar(opciones[j].valor);
    refs.current[j]?.focus();
  }

  return (
    <div className={`segmentado${rejilla ? " rejilla" : ""}`} role="radiogroup" aria-label={etiqueta}>
      {opciones.map((o, i) => (
        <button
          key={o.valor} type="button" role="radio" aria-checked={i === sel}
          ref={(el) => { refs.current[i] = el; }}
          tabIndex={i === sel || (sel < 0 && i === 0) ? 0 : -1}
          onClick={() => alCambiar(o.valor)} onKeyDown={(e) => teclas(e, i)}
        >
          {o.etiqueta}
        </button>
      ))}
    </div>
  );
}
