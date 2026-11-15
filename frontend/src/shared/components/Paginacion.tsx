import { useTranslation } from "../../i18n";

interface Props {
  pagina: number;        // 1..totalPaginas
  total: number;         // total de elementos
  porPagina: number;
  alCambiar: (pagina: number) => void;
  etiqueta: string;
}

/** Numeros de pagina con puntos suspensivos: 1 ... 4 5 [6] 7 8 ... 20 */
function paginas(actual: number, ultima: number): (number | "…")[] {
  if (ultima <= 7) return Array.from({ length: ultima }, (_, i) => i + 1);
  const set = new Set([1, 2, actual - 1, actual, actual + 1, ultima - 1, ultima].filter((n) => n >= 1 && n <= ultima));
  const orden = [...set].sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  orden.forEach((n, i) => { if (i && n - orden[i - 1] > 1) out.push("…"); out.push(n); });
  return out;
}

/** Paginacion accesible: anterior / numeros / siguiente y "Mostrando a-b de N". */
export default function Paginacion({ pagina, total, porPagina, alCambiar, etiqueta }: Props) {
  const { t } = useTranslation("sistema");
  const ultima = Math.max(1, Math.ceil(total / porPagina));
  if (total <= porPagina) return null;
  const desde = (pagina - 1) * porPagina + 1, hasta = Math.min(total, pagina * porPagina);
  return (
    <nav className="paginacion" aria-label={etiqueta}>
      <span className="paginacion-info" aria-live="polite">{t("audit.page.showing", { desde, hasta, total })}</span>
      <div className="paginacion-botones">
        <button type="button" className="pag-btn" disabled={pagina <= 1} onClick={() => alCambiar(pagina - 1)}>‹ {t("audit.page.prev")}</button>
        {paginas(pagina, ultima).map((n, i) => n === "…"
          ? <span key={`e${i}`} className="pag-elipsis" aria-hidden="true">…</span>
          : <button key={n} type="button" className={`pag-btn num${n === pagina ? " activo" : ""}`} aria-current={n === pagina ? "page" : undefined} aria-label={t("audit.page.of", { p: n, t: ultima })} onClick={() => alCambiar(n)}>{n}</button>)}
        <button type="button" className="pag-btn" disabled={pagina >= ultima} onClick={() => alCambiar(pagina + 1)}>{t("audit.page.next")} ›</button>
      </div>
    </nav>
  );
}
