import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "../../../i18n";
import Paginacion from "../../../shared/components/Paginacion";
import type { EventoAuditoria } from "../types/sistema";

export interface Parseado { objetivo: string; detalle: Record<string, unknown> }
export interface Campo { clave: string; valor: string; cambio: boolean }
export interface Comparacion { antes: Campo[]; despues: Campo[]; cambios: number }

export function leer(payload: string): Parseado {
  try {
    const o = JSON.parse(payload) as { objetivo?: string | null; detalle?: Record<string, unknown> };
    return { objetivo: o.objetivo ?? "", detalle: o.detalle && typeof o.detalle === "object" ? o.detalle : {} };
  } catch { return { objetivo: "", detalle: {} }; }
}
const texto = (v: unknown) => (typeof v === "string" ? v : JSON.stringify(v));
const iniciales = (s: string) => s.split(/[\s_-]+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("") || "?";

/**
 * Compara un evento con el anterior de la misma accion y objetivo (el servidor guarda solo los valores nuevos, asi que el
 * "antes" sale del evento previo). Cada campo se marca como cambiado si no existe en el otro lado o su valor es distinto.
 */
export function comparar(actual: Parseado, previo: Parseado | null): Comparacion {
  const claves = [...new Set([...Object.keys(previo?.detalle ?? {}), ...Object.keys(actual.detalle)])];
  const antes: Campo[] = [], despues: Campo[] = [];
  let cambios = 0;
  for (const k of claves) {
    const hayA = !!previo && k in previo.detalle, hayD = k in actual.detalle;
    const distinto = !hayA || !hayD || JSON.stringify(previo!.detalle[k]) !== JSON.stringify(actual.detalle[k]);
    if (distinto) cambios += hayA && hayD ? 1 : 1;
    if (hayA) antes.push({ clave: k, valor: texto(previo!.detalle[k]), cambio: distinto });
    if (hayD) despues.push({ clave: k, valor: texto(actual.detalle[k]), cambio: distinto });
  }
  return { antes, despues, cambios };
}

interface Props {
  eventos: EventoAuditoria[];
  accion: (a: string) => string;
  hora: (ts: string) => string;
  /** id de tripulante -> nombre, para mostrar quien hizo el cambio. */
  nombres?: Record<string, { nombre: string; rol: string }>;
  porPagina?: number;
}

/** Auditoria paginada; cada evento se abre en tres paneles: Antes, Despues y Quien hizo el cambio. */
export default function ListaAuditoria({ eventos, accion, hora, nombres = {}, porPagina = 10 }: Props) {
  const { t, locale } = useTranslation("sistema");
  const [pagina, setPagina] = useState(1);
  const orden = useMemo(() => [...eventos].sort((a, b) => b.id - a.id), [eventos]);
  const filas = useMemo(() => orden.map((e, i) => {
    const act = leer(e.payload);
    const prevEv = orden.slice(i + 1).find((x) => x.accion === e.accion && leer(x.payload).objetivo === act.objetivo) ?? null;
    return { e, act, prevEv, cmp: comparar(act, prevEv ? leer(prevEv.payload) : null) };
  }), [orden]);
  const ultima = Math.max(1, Math.ceil(filas.length / porPagina));
  useEffect(() => { if (pagina > ultima) setPagina(ultima); }, [pagina, ultima]);
  const visibles = filas.slice((pagina - 1) * porPagina, pagina * porPagina);
  const completa = (ts: string) => new Date(ts).toLocaleString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const panel = (campos: Campo[], vacio: string, tipo: "antes" | "despues") => (
    <div className={`aud-panel ${tipo}`}>
      <h4>{t(tipo === "antes" ? "audit.before" : "audit.after")}</h4>
      {campos.length === 0
        ? <p className="aud-vacio">{vacio}</p>
        : <dl>{campos.map((c) => (
          <div key={c.clave} className={c.cambio ? "cambio" : ""}>
            <dt>{c.clave}</dt><dd>{c.valor}</dd>
            {c.cambio && <span className="sr-only">{t(tipo === "antes" ? "audit.diff.del" : "audit.diff.add")}</span>}
          </div>))}</dl>}
    </div>
  );

  return (
    <>
      <ul className="auditoria-git">
        {visibles.map(({ e, act, prevEv, cmp }) => {
          const persona = nombres[e.actor];
          const quien = persona?.nombre ?? e.actor;
          return (
            <li key={e.id}>
              <details className="aud-evento">
                <summary>
                  <span className="aud-id">#{e.id}</span>
                  <span className="aud-info">
                    <strong>{accion(e.accion ?? "")}</strong>
                    <span className="suave">{quien}{act.objetivo ? ` → ${act.objetivo}` : ""}</span>
                  </span>
                  {cmp.cambios > 0 ? <span className="aud-delta" aria-label={t("audit.changes", { count: cmp.cambios })}>{t("audit.changes", { count: cmp.cambios })}</span> : <span />}
                  <time dateTime={e.ts}>{hora(e.ts)}</time>
                </summary>
                <div className="aud-paneles" role="group" aria-label={t("audit.diff.aria", { id: e.id })}>
                  {panel(cmp.antes, prevEv ? t("audit.noData") : t("audit.noBefore"), "antes")}
                  {panel(cmp.despues, t("audit.noData"), "despues")}
                  <div className="aud-panel quien">
                    <h4>{t("audit.who")}</h4>
                    <div className="aud-persona">
                      <span className="aud-avatar" aria-hidden="true">{iniciales(quien)}</span>
                      <div>
                        <strong>{quien}</strong>
                        <span className="suave">{persona ? `${persona.rol} · ${e.actor}` : t("audit.actorId", { id: e.actor })}</span>
                      </div>
                    </div>
                    <dl>
                      <div><dt>{t("audit.what")}</dt><dd>{accion(e.accion ?? "")}</dd></div>
                      {act.objetivo && <div><dt>{t("audit.target")}</dt><dd>{nombres[act.objetivo]?.nombre ?? act.objetivo}</dd></div>}
                      <div><dt>{t("audit.when")}</dt><dd>{completa(e.ts)}</dd></div>
                      <div><dt>{t("audit.event")}</dt><dd>#{e.id}{prevEv ? ` · ${t("audit.diff.vsPrev", { id: prevEv.id })}` : ` · ${t("audit.diff.new")}`}</dd></div>
                    </dl>
                  </div>
                </div>
              </details>
            </li>
          );
        })}
      </ul>
      <Paginacion pagina={pagina} total={filas.length} porPagina={porPagina} alCambiar={setPagina} etiqueta={t("audit.page.aria")} />
    </>
  );
}
