import { memo, useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import type { ApexOptions } from "apexcharts";
import Alerta from "../../../shared/components/Alerta";
import Grafica, { usePaleta } from "../../../shared/components/Grafica";
import type { RespuestaAnimo, SerieAnimo } from "../types/bienestar";

const DIAS = 14;
const NIVELES = [1, 2, 3, 4, 5] as const;
const BOCAS: Record<number, string> = {
  1: "M8.5 17.5c1-2 2.2-3 3.5-3s2.5 1 3.5 3", 2: "M9 16.8c.8-1.2 1.8-1.8 3-1.8s2.2.6 3 1.8",
  3: "M9 16h6", 4: "M9 15c.8 1.2 1.8 1.8 3 1.8s2.2-.6 3-1.8", 5: "M8 14.5c.9 2.4 2.2 3.5 4 3.5s3.1-1.1 4-3.5z",
};

function Cara({ n }: { n: number }) {
  return (
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" />
      <circle cx="9" cy="10" r=".6" fill="currentColor" /><circle cx="15" cy="10" r=".6" fill="currentColor" />
      <path d={BOCAS[n]} />
    </svg>
  );
}

const claveDia = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/** Promedio del animo por dia, en los ultimos DIAS dias (el ultimo es hoy). Varios registros del mismo dia se promedian. */
function porDia(serie: SerieAnimo) {
  const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
  const dias = Array.from({ length: DIAS }, (_, k) => { const d = new Date(hoy); d.setDate(hoy.getDate() - (DIAS - 1 - k)); return d; });
  const acum = new Map<string, number[]>();
  for (const p of serie.puntos) { const k = claveDia(new Date(p.ts)); acum.set(k, [...(acum.get(k) ?? []), p.valor]); }
  return dias.map((d) => { const v = acum.get(claveDia(d)); return { fecha: d, n: v?.length ?? 0, valor: v ? v.reduce((a, b) => a + b, 0) / v.length : null }; });
}

/** Barras por dia (ultimos 14) con ApexCharts: altura = animo promedio (1-5), color = nivel, media punteada y hoy resaltado. */
function Linea({ serie }: { serie: SerieAnimo }) {
  const { t, locale } = useTranslation("bienestar");
  const p = usePaleta();
  const dias = porDia(serie);
  const color = (v: number | null) => (v === null ? "transparent" : Math.round(v) <= 1 ? p.rojo : Math.round(v) === 2 ? p.amarillo : Math.round(v) === 3 ? p.smoke : p.verde);
  const fmt = new Intl.DateTimeFormat(locale, { weekday: "short", day: "numeric", month: "short" });
  const opciones: ApexOptions = {
    colors: dias.map((d) => color(d.valor)),
    plotOptions: { bar: { distributed: true, borderRadius: 6, borderRadiusApplication: "end", columnWidth: "58%" } },
    xaxis: {
      categories: dias.map((d) => String(d.fecha.getDate())),
      axisBorder: { show: false }, axisTicks: { show: false },
      labels: { rotate: 0, hideOverlappingLabels: false, style: { fontSize: "11px", colors: dias.map((_, k) => (k === DIAS - 1 ? p.ink : p.smoke)) } },
    },
    yaxis: { min: 0, max: 5, tickAmount: 5, labels: { formatter: (v) => String(Math.round(v)), style: { fontSize: "11px" } } },
    annotations: serie.media !== null ? { yaxis: [{ y: serie.media, borderColor: p.ink, strokeDashArray: 4, opacity: 0.55 }] } : {},
    tooltip: {
      x: { formatter: (_v, o) => fmt.format(dias[o?.dataPointIndex ?? 0].fecha) },
      y: { title: { formatter: () => "" }, formatter: (v, o) => `${Number(v).toFixed(1)} / 5${dias[o?.dataPointIndex ?? 0].n > 1 ? ` · ${dias[o?.dataPointIndex ?? 0].n}` : ""}` },
    },
    grid: { padding: { left: 4, right: 4, top: 0, bottom: 0 } },
  };
  return (
    <Grafica
      className="animo-linea" tipo="bar" altura={168}
      series={[{ name: "animo", data: dias.map((d) => (d.valor === null ? null : Number(d.valor.toFixed(1)))) }]}
      opciones={opciones}
      etiqueta={serie.media !== null ? t("animo.chart.ariaMedia", { dias: DIAS, media: serie.media }) : t("animo.chart.aria", { dias: DIAS })}
    />
  );
}

function AnimoDiario({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("bienestar");
  const [serie, setSerie] = useState<SerieAnimo | null | "no">(null);
  const [resp, setResp] = useState<RespuestaAnimo | null>(null);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const cargar = useCallback(
    () => api<SerieAnimo>(`/animo/${tripulanteId}?dias=${DIAS}`).then(setSerie).catch(() => setSerie("no")),
    [tripulanteId],
  );
  useEffect(() => { setSerie(null); setResp(null); cargar(); }, [cargar]);

  async function elegir(valor: number) {
    if (enviando) return;
    setEnviando(true); setError("");
    try {
      setResp(await post<RespuestaAnimo>("/animo", { tripulante_id: tripulanteId, valor }));
      cargar();
    } catch (e) { setError((e as Error).message); } finally { setEnviando(false); }
  }

  const deHoy = serie && serie !== "no" ? serie.puntos.filter((p) => new Date(p.ts).toDateString() === new Date().toDateString()) : [];
  const hoy = deHoy.length ? deHoy[deHoy.length - 1].valor : undefined;
  const actual = resp?.valor ?? hoy;
  const n = serie && serie !== "no" ? serie.puntos.length : 0;

  return (
    <section className="tarjeta pieza animo">
      <div className="animo-principal">
      <div className="pieza-cab">
        <div>
          <h2>{t("animo.title")}</h2>
          <p className="suave">{t("animo.hint")}</p>
        </div>
      </div>

      <div className="animo-caras" role="group" aria-label={t("animo.group")}>
        {NIVELES.map((v) => (
          <button key={v} type="button" className={`cara cara-${v}${actual === v ? " elegida" : ""}`} aria-pressed={actual === v} disabled={enviando || serie === "no"} onClick={() => elegir(v)}>
            <Cara n={v} /><span>{t(`animo.nivel.${v}`)}</span>
          </button>
        ))}
      </div>

      {error && <Alerta tono="error">{error}</Alerta>}
      {serie === "no" && !error && <Alerta tono="info" titulo={t("animo.unavailable.title")}>{t("animo.unavailable.body")}</Alerta>}
      {resp && (
        <div className="animo-resp">
          {(resp.bajo || resp.aviso_linea_base) ? (
            <Alerta tono="aviso" titulo={resp.bajo ? t("animo.low.title") : t("animo.shift.title")}>
              {resp.bajo ? t("animo.low.body") : t("animo.shift.body")}
            </Alerta>
          ) : <Alerta tono="ok" titulo={t("animo.saved.title")}>{t("animo.saved.body")}</Alerta>}
          {resp.capsulas.map((c) => (
            <article key={c.id} className="capsula"><strong>{c.titulo}</strong><p>{c.contenido_markdown}</p></article>
          ))}
        </div>
      )}

      </div>
      {serie && serie !== "no" && (
        <div className="animo-historial">
          <div className="animo-meta">
            <span className="campo-etiqueta">{t("animo.lastDays", { dias: DIAS })}</span>
            {serie.media !== null && <span className="animo-media-txt">{t("animo.mean")} <strong>{serie.media}</strong> / 5</span>}
          </div>
          {n === 0 ? <p className="vacio">{t("animo.empty")}</p> : <Linea serie={serie} />}
        </div>
      )}
    </section>
  );
}

export default memo(AnimoDiario);
