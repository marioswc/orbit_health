import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import Logo from "../shared/components/Logo";
import ToggleTema from "../shared/components/ToggleTema";
import type { Tema } from "../shared/hooks/useTema";

export type Vista = "monitor" | "bienestar" | "enlace" | "riesgos" | "historial";

const ICONO = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

const VISTAS: { id: Vista; etiqueta: string; icono: ReactNode }[] = [
  { id: "monitor", etiqueta: "Monitor", icono: <svg {...ICONO}><path d="M3 12h4l2.5-7 4 14 2.5-7H21" /></svg> },
  { id: "bienestar", etiqueta: "Bienestar", icono: <svg {...ICONO}><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg> },
  { id: "historial", etiqueta: "Historial", icono: <svg {...ICONO}><path d="M4 19V5M4 19h16" /><path d="m7.5 14 3.5-4 3 2.5 4.5-6" /></svg> },
  { id: "riesgos", etiqueta: "Riesgos", icono: <svg {...ICONO}><path d="M12 3 4.5 6v5.5c0 4.4 3 7.9 7.5 9.5 4.5-1.6 7.5-5.1 7.5-9.5V6L12 3z" /><path d="M12 8.5v4M12 15.5v.1" /></svg> },
  { id: "enlace", etiqueta: "Enlace", icono: <svg {...ICONO}><path d="M4.5 10a11 11 0 0 1 15 0M7.5 13.5a6.5 6.5 0 0 1 9 0" /><circle cx="12" cy="17.5" r="1.2" fill="currentColor" stroke="none" /></svg> },
];

interface Props {
  vista: Vista;
  alCambiarVista: (v: Vista) => void;
  tema: Tema;
  alAlternarTema: () => void;
  /** Selector de tripulante (lo compone App para no acoplar esta barra a una feature). */
  selector: ReactNode;
}

/** Cabecera: marca a la izquierda, vistas al centro; tripulante y tema a la derecha. */
export default function BarraSuperior({ vista, alCambiarVista, tema, alAlternarTema, selector }: Props) {
  // Indicador deslizante bajo la vista activa (solo transform/width: no repinta el resto de la barra)
  const nav = useRef<HTMLElement>(null);
  const [ind, setInd] = useState({ x: 0, w: 0, listo: false });
  useLayoutEffect(() => {
    const medir = () => {
      const b = nav.current?.querySelector<HTMLElement>(".nav-item.activo");
      if (b) setInd({ x: b.offsetLeft, w: b.offsetWidth, listo: true });
    };
    medir();
    window.addEventListener("resize", medir);
    document.fonts?.ready.then(medir);
    return () => window.removeEventListener("resize", medir);
  }, [vista]);

  return (
    <header className="barra">
      <span className="marca"><Logo /><span className="texto-nav">ORBIT Health</span></span>

      <nav aria-label="Vistas" className={`barra-nav${ind.listo ? " con-indicador" : ""}`} ref={nav}>
        <span className="nav-indicador" aria-hidden="true" style={{ transform: `translateX(${ind.x}px)`, width: ind.w }} />
        {VISTAS.map((v) => (
          <button key={v.id} type="button" className={`nav-item${vista === v.id ? " activo" : ""}`} aria-current={vista === v.id ? "page" : undefined} aria-label={v.etiqueta} onClick={() => alCambiarVista(v.id)}>
            {v.icono}<span className="texto-nav">{v.etiqueta}</span>
          </button>
        ))}
      </nav>

      <div className="barra-acciones">
        {selector}
        <ToggleTema tema={tema} alternar={alAlternarTema} />
      </div>
    </header>
  );
}
