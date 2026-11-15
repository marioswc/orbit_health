import { memo, useMemo } from "react";
import type { ApexOptions } from "apexcharts";
import { useTranslation } from "../../../i18n";
import { num } from "../../../shared/formato";
import Grafica, { colorNivel, usePaleta } from "../../../shared/components/Grafica";
import type { SerieHistorial } from "../types/estado";

interface Props {
  serie: SerieHistorial | null;
  cargando: boolean;
  error: string;
  alCerrar: () => void;
  /** Para columnas angostas: grafica mas alta (el texto no se encoge al escalar). */
  compacta?: boolean;
}

const hora = (ts: string) => new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(ts) ? `${ts.replace(" ", "T")}Z` : ts).getTime();
const fechaCorta = (ms: number, locale: string) => new Date(ms).toLocaleDateString(locale, { day: "numeric", month: "short" });
const fechaLarga = (ms: number, locale: string) => new Date(ms).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const MAX_MARCADORES = 240;

/** Grafica de la serie de un indicador con ApexCharts: area con curva suave, media punteada, puntos por estado y tooltip con valor, fecha y nivel. */
function GraficaSerie({ serie, cargando, error, alCerrar, compacta = false }: Props) {
  const { t, locale } = useTranslation("monitor");
  const p = usePaleta();
  const puntos = useMemo(() => serie?.puntos ?? [], [serie]);

  const datos = useMemo(() => puntos.map((pt) => ({ x: hora(pt.ts), y: pt.valor })), [puntos]);

  const opciones = useMemo<ApexOptions>(() => {
    const ultimo = puntos.length - 1;
    const marcadores = puntos.length <= MAX_MARCADORES
      ? puntos.map((pt, i) => ({ seriesIndex: 0, dataPointIndex: i, fillColor: colorNivel(p, pt.nivel), strokeColor: p.fondo, size: i === ultimo ? 6 : 4 }))
      : [{ seriesIndex: 0, dataPointIndex: ultimo, fillColor: colorNivel(p, puntos[ultimo]?.nivel ?? ""), strokeColor: p.fondo, size: 6 }];
    const unidad = serie?.unidad ?? "";
    return {
      colors: [p.hud],
      stroke: { curve: "monotoneCubic", width: 2.5, lineCap: "round" },
      fill: { type: "gradient", gradient: { shadeIntensity: 1, opacityFrom: 0.34, opacityTo: 0, stops: [0, 100] } },
      markers: { size: 0, hover: { size: 7 }, discrete: marcadores },
      xaxis: {
        type: "datetime", tickAmount: compacta ? 3 : 5,
        axisBorder: { show: false }, axisTicks: { show: false }, tooltip: { enabled: false },
        labels: { datetimeUTC: false, rotate: 0, style: { fontSize: "11px" }, formatter: (v) => fechaCorta(Number(v), locale) },
      },
      yaxis: { forceNiceScale: true, tickAmount: 4, labels: { style: { fontSize: "11px" }, formatter: (v) => String(Number(Number(v).toFixed(2))) } },
      annotations: serie?.resumen.media !== undefined ? { yaxis: [{ y: serie.resumen.media, borderColor: p.ink, strokeDashArray: 4, opacity: 0.5 }] } : {},
      grid: { padding: { left: 8, right: 14, top: 6, bottom: 0 } },
      tooltip: {
        custom: ({ dataPointIndex }: { dataPointIndex: number }) => {
          const pt = puntos[dataPointIndex];
          if (!pt) return "";
          return `<div class="serie-tip-apex"><strong>${num(pt.valor)} ${unidad}</strong><span>${fechaLarga(hora(pt.ts), locale)}</span><span class="badge ${pt.nivel}">${t(`common:status.${pt.nivel}`)}</span></div>`;
        },
      },
    };
  }, [puntos, p, serie, locale, compacta, t]);

  if (!serie && !cargando && !error) return null;

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
      {!cargando && !error && puntos.length > 0 && (
        <Grafica
          className="serie-caja" tipo="area" altura={compacta ? 280 : 260}
          series={[{ name: serie?.etiqueta ?? "", data: datos }]}
          opciones={opciones}
          etiqueta={t("serie.graficaAria", { nombre: serie?.etiqueta ?? t("serie.indicador"), n: puntos.length })}
        />
      )}
    </section>
  );
}

export default memo(GraficaSerie);
