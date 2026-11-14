import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useTranslation } from "../../i18n";

interface Props {
  abierto: boolean;
  alCerrar: () => void;
  titulo: string;
  children: ReactNode;
}

const ENFOCABLES = 'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [role="combobox"], [tabindex]:not([tabindex="-1"])';

/** Panel lateral deslizante (dialogo modal): Escape o clic fuera lo cierran, el foco queda atrapado y vuelve al abrir. */
export default function Drawer({ abierto, alCerrar, titulo, children }: Props) {
  const panel = useRef<HTMLDivElement>(null);
  const id = useId();
  const { t } = useTranslation();

  useEffect(() => {
    if (!abierto) return;
    const previo = document.activeElement as HTMLElement | null;
    const raiz = panel.current;
    // el primer campo recibe el foco; si no hay, el propio panel
    (raiz?.querySelector<HTMLElement>(`.drawer-cuerpo :is(${ENFOCABLES})`) ?? raiz)?.focus();

    const teclas = (e: KeyboardEvent) => {
      if (e.key === "Escape") { e.stopPropagation(); alCerrar(); return; }
      if (e.key !== "Tab" || !raiz) return;
      const lista = Array.from(raiz.querySelectorAll<HTMLElement>(ENFOCABLES));
      if (lista.length === 0) { e.preventDefault(); return; }
      const primero = lista[0], ultimo = lista[lista.length - 1];
      if (e.shiftKey && document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
      else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
    };
    document.addEventListener("keydown", teclas);
    return () => { document.removeEventListener("keydown", teclas); previo?.focus?.(); };
  }, [abierto, alCerrar]);

  if (!abierto) return null;
  return createPortal(
    <div className="drawer-fondo" onMouseDown={(e) => { if (e.target === e.currentTarget) alCerrar(); }}>
      <div className="drawer" role="dialog" aria-modal="true" aria-labelledby={id} ref={panel} tabIndex={-1}>
        <header className="drawer-cabecera">
          <h2 id={id}>{titulo}</h2>
          <button type="button" className="ghost icono" onClick={alCerrar} aria-label={t("actions.close")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
          </button>
        </header>
        <div className="drawer-cuerpo">{children}</div>
      </div>
    </div>,
    document.body,
  );
}
