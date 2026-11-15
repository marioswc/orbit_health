import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

export interface Pestana { id: string; etiqueta: string }

interface Props {
  pestanas: Pestana[];
  valor: string;
  alCambiar: (id: string) => void;
  /** Nombre accesible de la lista de pestanas. */
  etiqueta: string;
  /** Contenido de la pestana activa. */
  children: ReactNode;
}

/** Pestanas accesibles (tablist): flechas/Inicio/Fin para moverse, foco rotatorio y un panel por pestana activa. */
export default function Pestanas({ pestanas, valor, alCambiar, etiqueta, children }: Props) {
  const base = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const idTab = (id: string) => `${base}-tab-${id}`;
  const idPanel = (id: string) => `${base}-panel-${id}`;

  function teclas(e: KeyboardEvent, i: number) {
    let j = i;
    if (e.key === "ArrowRight") j = (i + 1) % pestanas.length;
    else if (e.key === "ArrowLeft") j = (i - 1 + pestanas.length) % pestanas.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = pestanas.length - 1;
    else return;
    e.preventDefault();
    alCambiar(pestanas[j].id);
    refs.current[j]?.focus();
  }

  return (
    <div className="pestanas">
      <div className="pestanas-lista" role="tablist" aria-label={etiqueta}>
        {pestanas.map((p, i) => {
          const activa = p.id === valor;
          return (
            <button key={p.id} ref={(el) => { refs.current[i] = el; }} type="button" role="tab" id={idTab(p.id)} className="pestana"
              aria-selected={activa} aria-controls={idPanel(valor)} tabIndex={activa ? 0 : -1}
              onClick={() => alCambiar(p.id)} onKeyDown={(e) => teclas(e, i)}>
              {p.etiqueta}
            </button>
          );
        })}
      </div>
      <div className="pestanas-panel" role="tabpanel" id={idPanel(valor)} aria-labelledby={idTab(valor)} tabIndex={0}>
        {children}
      </div>
    </div>
  );
}
