import { memo, useId, useMemo, useState, type PointerEvent } from "react";
import { useTranslation } from "../../../i18n";
import type { SerieHistorial } from "../types/estado";

interface Props {
  serie: SerieHistorial | null;
  cargando: boolean;
  error: string;
  alCerrar: () => void;
}

const W = 640, H = 250, ML = 46, MR = 16, MT = 16, MB = 30;
const hora = (ts: string) => new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(ts) ? `${ts.replace(" ", "T")}Z` : ts).getTime();
const fechaCorta = (ms: number, locale: string) => new Date(ms).toLocaleDateString(locale, { day: "numeric", month: "short" });
const fechaLarga = (ms: number, locale: string) => new Date(ms).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

/** Escala "bonita": 4 marcas con paso redondo que cubren [min, max]. */
function marcas(min: number, max: number): number[] {
  const rango = Math.max(max - min, 1e-9);
  const bruto = rango / 3;
  const pot = 10 ** Math.floor(Math.log10(bruto));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * pot).find((p) => p >= bruto) ?? bruto;
  const ini = Math.floor(min / paso) * paso;
  const out: number[] = [];
  for (let v = ini; v < max + paso * 0.999 && out.length < 6; v += paso) out.push(Number(v.toFixed(6)));
  return out;
}

/** Curva suave que no sobrepasa los datos (Fritsch-Carlson / monotona). */
function curva(p: { x: number; y: number }[]): string {
  if (p.length < 2) return "";
  const n = p.length;
  const dx: number[] = [], m: number[] = [];
  for (let i = 0; i < n - 1; i++) { dx.push(p[i + 1].x - p[i].x || 1e-9); m.push((p[i + 1].y - p[i].y) / dx[i]); }
  const t = [m[0]];
  for (let i = 1; i < n - 1; i++) t.push(m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2);
  t.push(m[n - 2]);
  for (let i = 0; i < n - 1; i++) {
    if (m[i] === 0) { t[i] = 0; t[i + 1] = 0; continue; }
    const a = t[i] / m[i], b = t[i + 1] / m[i], s = a * a + b * b;
    if (s > 9) { const k = 3 / Math.sqrt(s); t[i] = k * a * m[i]; t[i + 1] = k * b * m[i]; }
  }
  let d = `M${p[0].x.toFixed(1)} ${p[0].y.toFixed(1)}`;
  for (let i = 0; i < n - 1; i++) {
    const h = dx[i] / 3;
    d += ` C${(p[i].x + h).toFixed(1)} ${(p[i].y + t[i] * h).toFixed(1)} ${(p[i + 1].x - h).toFixed(1)} ${(p[i + 1].y - t[i + 1] * h).toFixed(1)} ${p[i + 1].x.toFixed(1)} ${p[i + 1].y.toFixed(1)}`;
  }
  return d;
}

/** Grafica SVG de la serie de un indicador: ejes con escala, curva suave con area, media, tooltip y puntos por estado. Sin librerias. */
function GraficaSerie({ serie, cargando, error, alCerrar }: Props) {
  const { t, locale } = useTranslation("monitor");
  const [sel, setSel] = useState<number | null>(null);
  const idGrad = useId().replace(/:/g, "");
  const puntos = serie?.puntos ?? [];

  const g = useMemo(() => {
    if (puntos.length === 0) return null;
    const ts = puntos.map((p) => hora(p.ts));
    const vals = puntos.map((p) => p.valor);
    let t0 = Math.min(...ts), t1 = Math.max(...ts);
    if (t1 === t0) { t0 -= 3600000; t1 += 3600000; }
    const vmin = Math.min(...vals), vmax = Math.max(...vals);
    const ticks = marcas(vmin === vmax ? vmin - 1 : vmin, vmax === vmin ? vmax + 1 : vmax);
    const y0 = ticks[0], y1 = ticks[ticks.length - 1];
    const x = (t: number) => ML + ((t - t0) / (t1 - t0)) * (W - ML - MR);
    const y = (v: number) => MT + (1 - (v - y0) / (y1 - y0 || 1)) * (H - MT - MB);
    const pts = puntos.map((p, i) => ({ x: x(ts[i]), y: y(p.valor), p, t: ts[i] }));
    const linea = curva(pts);
    const area = pts.length > 1 ? `${linea} L${pts[pts.length - 1].x.toFixed(1)} ${H - MB} L${pts[0].x.toFixed(1)} ${H - MB} Z` : "";
    const xs = [t0, (t0 + t1) / 2, t1];
    return { pts, linea, area, ticks, y, x, xs };
  }, [puntos]);

  if (!serie && !cargando && !error) return null;

  function mover(e: PointerEvent<SVGSVGElement>) {
    if (!g) return;
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    let mejor = 0;
    g.pts.forEach((p, i) => { if (Math.abs(p.x - px) < Math.abs(g.pts[mejor].x - px)) mejor = i; });
    setSel(mejor);
  }
  const s = g && sel !== null ? g.pts[sel] : null;
  const media = serie?.resumen.media;

  return (
    <section className="tarjeta grafica-serie" aria-label={t("serie.aria")}>
      <div className="grafica-cab">
        <div>
          <h2>{serie ? t("serie.titulo", { etiqueta: serie.etiqueta, dias: serie.dias }) : t("serie.tituloVacio")}</h2>
          {serie && (
            <p className="suave">
              {t("serie.lecturas", { count: serie.resumen.n })}
              {serie.resumen.n > 0 && t("serie.resumen", { min: serie.resumen.min, media: serie.resumen.media, max: serie.resumen.max, unidad: serie.unidad })}
            </p>
          )}
        </div>
        <button type="button" className="ghost" onClick={alCerrar}>{t("serie.cerrar")}</button>
      </div>

      {cargando && <span className="esqueleto" style={{ height: 200 }} aria-busy="true" />}
      {error && <p className="error">{error}</p>}
      {!cargando && !error && serie && puntos.length === 0 && <p className="suave">{t("serie.sinLecturas")}</p>}
      {!cargando && !error && g && (
        <div className="serie-caja">
          <svg className="serie-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={t("serie.graficaAria", { nombre: serie?.etiqueta ?? t("serie.indicador"), n: puntos.length })}
            onPointerMove={mover} onPointerLeave={() => setSel(null)}>
            <defs>
              <linearGradient id={idGrad} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--hud)" stopOpacity=".28" /><stop offset="100%" stopColor="var(--hud)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {g.ticks.map((v) => (
              <g key={v}>
                <line className="serie-rejilla" x1={ML} x2={W - MR} y1={g.y(v)} y2={g.y(v)} />
                <text className="serie-txt" x={ML - 8} y={g.y(v)} textAnchor="end" dominantBaseline="middle">{Number(v.toFixed(2))}</text>
              </g>
            ))}
            {g.xs.map((tk, i) => <text key={i} className="serie-txt" x={g.x(tk)} y={H - 8} textAnchor={i === 0 ? "start" : i === 2 ? "end" : "middle"}>{fechaCorta(tk, locale)}</text>)}
            {media !== undefined && <line className="serie-media" x1={ML} x2={W - MR} y1={g.y(media)} y2={g.y(media)} />}
            {g.area && <path d={g.area} fill={`url(#${idGrad})`} />}
            {g.pts.length > 1 && <path className="serie-linea" d={g.linea} fill="none" pathLength={1} />}
            {s && <line className="serie-guia" x1={s.x} x2={s.x} y1={MT} y2={H - MB} />}
            {g.pts.map((c, i) => (
              <circle key={`${c.p.ts}-${i}`} className={`serie-punto ${c.p.nivel}${i === g.pts.length - 1 ? " ultimo" : ""}${sel === i ? " sel" : ""}`} cx={c.x} cy={c.y} r={sel === i ? 6 : i === g.pts.length - 1 ? 5 : g.pts.length > 40 ? 2.2 : 3.6} />
            ))}
          </svg>
          {s && (
            <div className="serie-tip" style={{ left: `${(s.x / W) * 100}%`, top: `${(s.y / H) * 100}%` }} role="status">
              <strong>{s.p.valor} {serie?.unidad}</strong>
              <span>{fechaLarga(s.t, locale)}</span>
              <span className={`badge ${s.p.nivel}`}>{t(`common:status.${s.p.nivel}`)}</span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default memo(GraficaSerie);
