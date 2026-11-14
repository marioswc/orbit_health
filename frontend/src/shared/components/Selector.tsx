import { useTranslation } from "../../i18n";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

export interface Opcion { valor: string; etiqueta: string }

interface Props {
  opciones: Opcion[];
  valor: string;
  alCambiar: (valor: string) => void;
  etiqueta: string; // nombre accesible
  marcador?: string;
  className?: string;
}

/** Lista desplegable accesible (combobox + listbox) con el diseno de la app. */
export default function Selector({ opciones, valor, alCambiar, etiqueta, marcador, className = "" }: Props) {
  const { t } = useTranslation("shared");
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(0);
  const raiz = useRef<HTMLDivElement>(null);
  const boton = useRef<HTMLButtonElement>(null);
  const id = useId();
  const sel = opciones.findIndex((o) => o.valor === valor);

  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => { if (!raiz.current?.contains(e.target as Node)) setAbierto(false); };
    document.addEventListener("mousedown", fuera);
    return () => document.removeEventListener("mousedown", fuera);
  }, [abierto]);

  useEffect(() => {
    if (abierto) document.getElementById(`${id}-${activo}`)?.scrollIntoView({ block: "nearest" });
  }, [abierto, activo, id]);

  function abrir() { setActivo(sel >= 0 ? sel : 0); setAbierto(true); }
  function elegir(i: number) { alCambiar(opciones[i].valor); setAbierto(false); boton.current?.focus(); }

  function teclas(e: KeyboardEvent) {
    if (!abierto) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) { e.preventDefault(); abrir(); }
      return;
    }
    if (e.key === "Escape") { e.preventDefault(); setAbierto(false); }
    else if (e.key === "ArrowDown") { e.preventDefault(); setActivo((a) => Math.min(a + 1, opciones.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActivo((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Home") { e.preventDefault(); setActivo(0); }
    else if (e.key === "End") { e.preventDefault(); setActivo(opciones.length - 1); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); elegir(activo); }
    else if (e.key === "Tab") setAbierto(false);
  }

  return (
    <div className={`selector ${className}`} ref={raiz}>
      <button
        ref={boton} type="button" role="combobox" className="selector-boton"
        aria-haspopup="listbox" aria-expanded={abierto} aria-controls={`${id}-lista`} aria-label={etiqueta}
        aria-activedescendant={abierto ? `${id}-${activo}` : undefined}
        onClick={() => (abierto ? setAbierto(false) : abrir())} onKeyDown={teclas}
      >
        <span className={sel < 0 ? "marcador" : undefined}>{sel >= 0 ? opciones[sel].etiqueta : (marcador ?? t("selector.placeholder"))}</span>
        <svg className="selector-flecha" width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M1 1.5l5 5 5-5" /></svg>
      </button>
      {abierto && (
        <ul className="selector-lista" role="listbox" id={`${id}-lista`} aria-label={etiqueta}>
          {opciones.map((o, i) => (
            <li
              key={o.valor} id={`${id}-${i}`} role="option" aria-selected={i === sel}
              className={`${i === activo ? "activa" : ""} ${i === sel ? "elegida" : ""}`}
              onMouseEnter={() => setActivo(i)} onMouseDown={(e) => e.preventDefault()} onClick={() => elegir(i)}
            >
              <span>{o.etiqueta}</span>
              {i === sel && <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2.5 7.5l3 3 6-7" /></svg>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
