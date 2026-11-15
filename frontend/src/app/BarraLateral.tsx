import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "../i18n";
import Logo from "../shared/components/Logo";

export type Vista = "monitor" | "bienestar" | "enlace" | "riesgos" | "historial" | "sistema" | "banda" | "asistente";

const ICONO = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;

export const VISTAS: { id: Vista; etiqueta: string; icono: ReactNode }[] = [
  { id: "monitor", etiqueta: "Monitor", icono: <svg {...ICONO}><path d="M3 12h4l2.5-7 4 14 2.5-7H21" /></svg> },
  { id: "banda", etiqueta: "Banda", icono: <svg {...ICONO}><rect x="7" y="6.5" width="10" height="11" rx="3" /><path d="M9 6.5 9.8 3h4.4l.8 3.5M9 17.5 9.8 21h4.4l.8-3.5M12 10v2.4l1.6 1" /></svg> },
  { id: "historial", etiqueta: "Historial", icono: <svg {...ICONO}><path d="M4 19V5M4 19h16" /><path d="m7.5 14 3.5-4 3 2.5 4.5-6" /></svg> },
  { id: "bienestar", etiqueta: "Bienestar", icono: <svg {...ICONO}><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" /></svg> },
  { id: "asistente", etiqueta: "Asistente", icono: <svg {...ICONO}><path d="M12 3.5 13.9 9l5.6 1.9-5.6 1.9L12 18.3l-1.9-5.5L4.5 10.9 10.1 9z" /><path d="M18.5 15.5v4M16.5 17.5h4" /></svg> },
  { id: "riesgos", etiqueta: "Riesgos", icono: <svg {...ICONO}><path d="M12 3 4.5 6v5.5c0 4.4 3 7.9 7.5 9.5 4.5-1.6 7.5-5.1 7.5-9.5V6L12 3z" /><path d="M12 8.5v4M12 15.5v.1" /></svg> },
  { id: "enlace", etiqueta: "Enlace", icono: <svg {...ICONO}><path d="M4.5 10a11 11 0 0 1 15 0M7.5 13.5a6.5 6.5 0 0 1 9 0" /><circle cx="12" cy="17.5" r="1.2" fill="currentColor" stroke="none" /></svg> },
  { id: "sistema", etiqueta: "Sistema", icono: <svg {...ICONO}><rect x="4" y="5" width="16" height="6" rx="2" /><rect x="4" y="13" width="16" height="6" rx="2" /><path d="M8 8h.1M8 16h.1" /></svg> },
];

const CLAVE = "orbit-lateral";

interface Props {
  vista: Vista;
  alCambiarVista: (v: Vista) => void;
  /** Aviso fijo al pie (prototipo / umbrales). Lo compone App. */
  aviso?: { titulo: string; texto: string } | null;
}

/** Menu lateral: marca, vistas (con indicador deslizante), colapsable, y aviso del prototipo al pie. En movil pasa a barra inferior. */
export default function BarraLateral({ vista, alCambiarVista, aviso }: Props) {
  const { t } = useTranslation();
  const [colapsada, setColapsada] = useState(() => {
    const q = new URLSearchParams(window.location.search).get("lateral"); // ?lateral=1|0 fuerza el estado (ensayos y capturas)
    if (q === "1" || q === "0") return q === "1";
    try { return localStorage.getItem(CLAVE) === "1"; } catch { return false; }
  });
  const nav = useRef<HTMLElement>(null);
  const [ind, setInd] = useState({ y: 0, h: 0, listo: false });

  useLayoutEffect(() => {
    const medir = () => {
      const b = nav.current?.querySelector<HTMLElement>(".lateral-item.activo");
      if (b) setInd({ y: b.offsetTop, h: b.offsetHeight, listo: true });
    };
    medir();
    window.addEventListener("resize", medir);
    document.fonts?.ready.then(medir);
    return () => window.removeEventListener("resize", medir);
  }, [vista, colapsada]);

  function alternar() {
    setColapsada((c) => { try { localStorage.setItem(CLAVE, c ? "0" : "1"); } catch { /* sin almacenamiento */ } return !c; });
  }

  return (
    <aside className={`lateral${colapsada ? " colapsada" : ""}`} aria-label={t("nav.menu")}>
      <div className="lateral-cab">
        <span className="marca"><Logo /><span className="texto-nav">ORBIT Health</span></span>
      </div>

      <nav aria-label={t("nav.views")} className={`lateral-nav${ind.listo ? " con-indicador" : ""}`} ref={nav}>
        <span className="lateral-indicador" aria-hidden="true" style={{ transform: `translateY(${ind.y}px)`, height: ind.h }} />
        {VISTAS.map((v) => (
          <button key={v.id} type="button" className={`lateral-item${vista === v.id ? " activo" : ""}`} aria-current={vista === v.id ? "page" : undefined} aria-label={t(`nav.${v.id}`)} title={colapsada ? t(`nav.${v.id}`) : undefined} onClick={() => alCambiarVista(v.id)}>
            {v.icono}<span className="texto-nav">{t(`nav.${v.id}`)}</span>
          </button>
        ))}
      </nav>

      {aviso && (
        <div className="lateral-aviso" role="note" title={`${aviso.titulo}. ${aviso.texto}`}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 4 3 19.5h18L12 4z" /><path d="M12 10v4.5M12 17.2v.1" /></svg>
          <div className="texto-nav"><strong>{aviso.titulo}</strong><span>{aviso.texto}</span></div>
        </div>
      )}

      <button type="button" className="lateral-colapsar" onClick={alternar} aria-label={colapsada ? t("nav.expand") : t("nav.collapse")} aria-pressed={colapsada} title={colapsada ? t("nav.expand") : undefined}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m14.5 6-6 6 6 6" /></svg>
        <span className="texto-nav">{t("nav.collapseShort")}</span>
      </button>
    </aside>
  );
}
