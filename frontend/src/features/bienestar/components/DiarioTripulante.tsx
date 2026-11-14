import { FormEvent, memo, useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Drawer from "../../../shared/components/Drawer";
import Segmentado from "../../../shared/components/Segmentado";
import Selector from "../../../shared/components/Selector";
import type { NotaDiario } from "../types/bienestar";

type Periodo = "todas" | "hoy" | "ayer" | "7d" | "mes";
const PERIODOS: Periodo[] = ["todas", "hoy", "ayer", "7d"];

/** El servidor manda "YYYY-MM-DD HH:MM:SS" en UTC sin zona; sin esto el navegador lo tomaria como hora local. */
const fecha = (ts: string) => new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$/.test(ts) ? `${ts.replace(" ", "T")}Z` : ts);
const inicioDia = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const mismoDia = (a: Date, b: Date) => inicioDia(a).getTime() === inicioDia(b).getTime();
const sinAcentos = (t: string) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
/** Fecha local "YYYY-MM-DD" (lo que entrega y espera <input type="date">). */
const aClave = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

const claveMes = (d: Date) => aClave(d).slice(0, 7);
const nombreMes = (clave: string, locale: string) => {
  const [a, m] = clave.split("-").map(Number);
  const t = new Date(a, m - 1, 1).toLocaleDateString(locale, { month: "long", year: "numeric" });
  return t.charAt(0).toUpperCase() + t.slice(1);
};

function enPeriodo(f: Date, periodo: Periodo): boolean {
  const hoy = new Date();
  switch (periodo) {
    case "hoy": return mismoDia(f, hoy);
    case "ayer": { const a = new Date(hoy); a.setDate(hoy.getDate() - 1); return mismoDia(f, a); }
    case "7d": { const d = inicioDia(hoy); d.setDate(d.getDate() - 6); return f >= d; }
    default: return true;
  }
}

function etiquetaDia(d: Date, locale: string, t: (k: string) => string): string {
  const hoy = new Date();
  const ayer = new Date(hoy); ayer.setDate(hoy.getDate() - 1);
  if (mismoDia(d, hoy)) return t("diario.today");
  if (mismoDia(d, ayer)) return t("diario.yesterday");
  return d.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", ...(d.getFullYear() !== hoy.getFullYear() && { year: "numeric" }) });
}

const hora = (f: Date, ts: string, locale: string) => (Number.isNaN(f.getTime()) ? ts.slice(11, 16) : f.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" }));

function DiarioTripulante({ tripulanteId }: { tripulanteId: string }) {
  const { t, locale } = useTranslation("bienestar");
  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [notas, setNotas] = useState<NotaDiario[] | null>(null);
  const [falloCarga, setFalloCarga] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);
  const [periodo, setPeriodo] = useState<Periodo>("todas");
  const [mes, setMes] = useState(""); // "YYYY-MM" o "" = todos
  const [busqueda, setBusqueda] = useState("");
  const [abierta, setAbierta] = useState<NotaDiario | null>(null);
  const cerrar = useCallback(() => setAbierta(null), []);

  const cargar = useCallback(
    () => api<NotaDiario[]>(`/diario/${tripulanteId}`).then((n) => { setNotas(n); setFalloCarga(false); }).catch(() => { setNotas((p) => p ?? []); setFalloCarga(true); }),
    [tripulanteId],
  );
  useEffect(() => { setNotas(null); setAbierta(null); cargar(); }, [cargar]);

  async function guardar(e: FormEvent) {
    e.preventDefault();
    if (!contenido.trim()) return setMsg({ ok: false, texto: t("diario.writeFirst") });
    try {
      await post("/diario", { tripulante_id: tripulanteId, titulo: titulo || null, contenido });
      setContenido(""); setTitulo("");
      setMsg({ ok: true, texto: t("diario.saved") });
      cargar();
    } catch (err) { setMsg({ ok: false, texto: (err as Error).message }); }
  }

  const filtrando = periodo !== "todas" || mes !== "" || busqueda.trim() !== "";
  const limpiar = () => { setPeriodo("todas"); setMes(""); setBusqueda(""); };

  // Meses que tienen notas (mas reciente primero), con su conteo
  const meses = useMemo(() => {
    const c = new Map<string, number>();
    for (const n of notas ?? []) {
      const f = fecha(n.ts);
      if (!Number.isNaN(f.getTime())) c.set(claveMes(f), (c.get(claveMes(f)) ?? 0) + 1);
    }
    return [...c.entries()].sort((a, b) => b[0].localeCompare(a[0]));
  }, [notas]);

  // Mas recientes primero, filtradas y agrupadas por dia
  const grupos = useMemo(() => {
    const q = sinAcentos(busqueda.trim());
    const orden = [...(notas ?? [])].sort((a, b) => fecha(b.ts).getTime() - fecha(a.ts).getTime())
      .filter((n) => {
        const f = fecha(n.ts);
        if (!Number.isNaN(f.getTime()) && (!enPeriodo(f, periodo) || (mes && claveMes(f) !== mes))) return false;
        return !q || sinAcentos(`${n.titulo ?? ""} ${n.contenido}`).includes(q);
      });
    const mapa = new Map<string, { etiqueta: string; notas: NotaDiario[] }>();
    for (const n of orden) {
      const f = fecha(n.ts);
      const k = Number.isNaN(f.getTime()) ? n.ts.slice(0, 10) : aClave(f);
      if (!mapa.has(k)) mapa.set(k, { etiqueta: Number.isNaN(f.getTime()) ? k : etiquetaDia(f, locale, t), notas: [] });
      mapa.get(k)!.notas.push(n);
    }
    return [...mapa.values()];
  }, [notas, periodo, mes, busqueda, locale, t]);
  const visibles = grupos.reduce((s, g) => s + g.notas.length, 0);
  const total = notas?.length ?? 0;

  const fAbierta = abierta ? fecha(abierta.ts) : null;

  return (
    <section className="tarjeta pieza diario">
      <div className="pieza-cab">
        <div>
          <h2>{t("diario.title")}</h2>
          <p className="suave">{t("diario.hint")}</p>
        </div>
        {total > 0 && <span className="conteo-notas">{t("diario.notes", { count: total })}</span>}
      </div>

      <form onSubmit={guardar} className="redactor">
        <label className="sr-only" htmlFor="diario-titulo">{t("diario.titleLabel")}</label>
        <input id="diario-titulo" className="redactor-titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder={t("diario.titleLabel")} maxLength={120} />
        <label className="sr-only" htmlFor="diario-texto">{t("diario.noteLabel")}</label>
        <textarea id="diario-texto" className="redactor-texto" value={contenido} onChange={(e) => setContenido(e.target.value)} placeholder={t("diario.notePlaceholder")} />
        <div className="redactor-pie">
          <span className="redactor-cuenta">{contenido.trim() ? t("diario.chars", { count: contenido.trim().length }) : t("diario.onlyYou")}</span>
          <button type="submit" className="btn-primario" disabled={!contenido.trim()}>{t("diario.save")}</button>
        </div>
      </form>
      {msg && <Alerta tono={msg.ok ? "ok" : "error"}>{msg.texto}</Alerta>}

      <div className="notas-barra" role="search" aria-label={t("diario.searchAria")}>
        <div className="notas-buscar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></svg>
          <input type="search" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder={t("diario.search")} aria-label={t("diario.search")} />
        </div>
        {meses.length > 0 && (
          <div className="notas-mes">
            <Selector
              etiqueta={t("diario.month")} valor={mes} alCambiar={(v) => { setMes(v); setPeriodo("todas"); }}
              opciones={[{ valor: "", etiqueta: t("diario.allMonths") }, ...meses.map(([k, n]) => ({ valor: k, etiqueta: `${nombreMes(k, locale)} · ${n}` }))]}
            />
          </div>
        )}
      </div>
      <Segmentado etiqueta={t("diario.period")} opciones={PERIODOS.map((p) => ({ valor: p, etiqueta: t(`diario.period.${p}`) }))} valor={periodo} alCambiar={(v) => { setPeriodo(v as Periodo); setMes(""); }} />

      {filtrando && notas && total > 0 && (
        <p className="notas-resumen" role="status">
          {t("diario.summary", { visibles, conteo: t("diario.notes", { count: total }) })} <button type="button" className="enlace" onClick={limpiar}>{t("diario.clear")}</button>
        </p>
      )}

      {falloCarga && <Alerta tono="error" titulo={t("diario.loadError.title")} accion={<button type="button" onClick={cargar}>{t("diario.retry")}</button>}>{t("diario.loadError.body")}</Alerta>}

      <div className="diario-feed">
        {notas === null ? (
          <><span className="esqueleto" style={{ height: 72 }} aria-busy="true" /><span className="esqueleto" style={{ height: 72 }} /></>
        ) : total === 0 ? (
          <p className="vacio">{t("diario.empty")}</p>
        ) : visibles === 0 ? (
          <p className="vacio">{t("diario.noMatch")} <button type="button" className="enlace" onClick={limpiar}>{t("diario.clear")}</button></p>
        ) : grupos.map((g) => (
          <div key={g.etiqueta} className="dia">
            <h3 className="dia-etiqueta">{g.etiqueta}</h3>
            <ol className="notas">
              {g.notas.map((n) => {
                const f = fecha(n.ts);
                return (
                  <li key={n.id} className="nota">
                    <time className="nota-hora" dateTime={n.ts}>{hora(f, n.ts, locale)}</time>
                    <button type="button" className="nota-cuerpo" onClick={() => setAbierta(n)} aria-haspopup="dialog">
                      <h4>{n.titulo ?? t("diario.untitled")}</h4>
                      <p>{n.contenido}</p>
                    </button>
                  </li>
                );
              })}
            </ol>
          </div>
        ))}
      </div>

      <Drawer abierto={!!abierta} alCerrar={cerrar} titulo={abierta?.titulo ?? t("diario.untitled")}>
        {abierta && fAbierta && (
          <article className="nota-lectura">
            <p className="nota-lectura-fecha">
              {Number.isNaN(fAbierta.getTime()) ? abierta.ts : `${fAbierta.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" })} · ${hora(fAbierta, abierta.ts, locale)}`}
            </p>
            <p className="nota-lectura-texto">{abierta.contenido}</p>
            <p className="nota-lectura-privada">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
              {t("diario.private")}
            </p>
          </article>
        )}
      </Drawer>
    </section>
  );
}

export default memo(DiarioTripulante);
