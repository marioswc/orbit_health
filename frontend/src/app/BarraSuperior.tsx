import type { ReactNode } from "react";
import Logo from "../shared/components/Logo";
import ToggleTema from "../shared/components/ToggleTema";
import type { Tema } from "../shared/hooks/useTema";

export type Vista = "monitor" | "bienestar" | "enlace";

const ICONO = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

const VISTAS: { id: Vista; etiqueta: string; icono: ReactNode }[] = [
  { id: "monitor", etiqueta: "Monitor", icono: <svg {...ICONO}><path d="M3 12h4l2.5-7 4 14 2.5-7H21" /></svg> },
  { id: "bienestar", etiqueta: "Bienestar", icono: <svg {...ICONO}><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg> },
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
  return (
    <header className="barra">
      <span className="marca"><Logo /><span className="texto-nav">ORBIT Health</span></span>

      <nav aria-label="Vistas" className="barra-nav">
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
