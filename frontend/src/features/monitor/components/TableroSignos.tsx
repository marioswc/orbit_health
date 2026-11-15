import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import type { LecturaEstado, PuntoHistorial } from "../types/estado";
import { nombreIndicador } from "../utils/nombreIndicador";
import type { ApexOptions } from "apexcharts";
import Grafica, { colorNivel, usePaleta } from "../../../shared/components/Grafica";

import { num } from "../../../shared/formato";
export { num };

const MAX_NEWS2 = 20; // escala real del puntaje NEWS2 (0 a 20)
const R = 54;
const CIRC = 2 * Math.PI * R;

/** Anillo NEWS2: se llena hasta el puntaje real y toma el color del nivel que calculo el backend. */
export const AnilloNews2 = memo(function AnilloNews2({ puntos, nivel, ventana }: { puntos: number; nivel: string; ventana: number }) {
  const { t } = useTranslation("consola");
  const [lleno, setLleno] = useState(0);
  useEffect(() => { const id = requestAnimationFrame(() => setLleno(Math.min(puntos, MAX_NEWS2) / MAX_NEWS2)); return () => cancelAnimationFrame(id); }, [puntos]);
  return (
    <div className={`anillo ${nivel}`} role="img" aria-label={t("news2.aria", { p: puntos })}>
      <svg viewBox="0 0 128 128">
        <circle className="anillo-pista" cx="64" cy="64" r={R} />
        <circle className="anillo-valor" cx="64" cy="64" r={R} strokeDasharray={CIRC} strokeDashoffset={CIRC * (1 - lleno)} transform="rotate(-90 64 64)" />
      </svg>
      <div className="anillo-centro"><strong>{puntos}</strong><span>{t("news2.scale", { max: MAX_NEWS2 })}</span></div>
      <p className="anillo-pie">{t("news2.window", { min: ventana })}</p>
    </div>
  );
});

/** Corazon que late a la ultima frecuencia cardiaca registrada (no es una señal en vivo). */
export const PulsoCardiaco = memo(function PulsoCardiaco({ lectura }: { lectura?: LecturaEstado }) {
  const { t } = useTranslation("consola");
  if (!lectura) return <p className="suave">{t("pulse.none")}</p>;
  const bpm = Math.min(220, Math.max(30, lectura.valor));
  return (
    <div className={`pulso ${lectura.nivel}`}>
      <svg className="corazon-latido" style={{ ["--lat" as string]: `${(60 / bpm).toFixed(2)}s` }} width="52" height="52" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z" /></svg>
      <div><strong>{num(lectura.valor)}</strong><span>{lectura.unidad}</span></div>
      <p className="suave">{t("pulse.note")}</p>
    </div>
  );
});

/** Mini grafica (ApexCharts, modo sparkline) de la serie real de un indicador; el color es el del nivel. */
export function Chispa({ puntos, nivel }: { puntos?: PuntoHistorial[]; nivel: string }) {
  const p = usePaleta();
  if (!puntos || puntos.length < 2) return <span className="chispa-vacia" aria-hidden="true" />;
  const opciones: ApexOptions = {
    chart: { sparkline: { enabled: true }, animations: { enabled: false } },
    colors: [colorNivel(p, nivel)],
    stroke: { curve: "monotoneCubic", width: 2, lineCap: "round" },
    fill: { type: "gradient", gradient: { shadeIntensity: 1, opacityFrom: 0.28, opacityTo: 0, stops: [0, 100] } },
    markers: { size: 0 },
    tooltip: { enabled: false },
    grid: { padding: { left: 0, right: 0, top: 2, bottom: 2 } },
  };
  return <Grafica className={`chispa ${nivel}`} tipo="area" altura={26} decorativa series={[{ name: "", data: puntos.map((q) => q.valor) }]} opciones={opciones} etiqueta="" />;
}

/** Lista de signos: valor actual, tendencia real de 14 dias y estado; al tocar una fila se elige para la grafica grande. */
export const SignosVitales = memo(function SignosVitales({ vitales, series, seleccionado, alElegir }: {
  vitales: LecturaEstado[]; series: Record<string, PuntoHistorial[]>; seleccionado: string | null; alElegir: (clave: string) => void;
}) {
  const { t } = useTranslation("consola");
  const { t: tm } = useTranslation("monitor");
  if (vitales.length === 0) return <p className="suave">{t("vitals.empty")}</p>;
  return (
    <ul className="vitales">
      {vitales.map((l, i) => (
        <li key={l.indicador} className={l.nivel} style={{ ["--i" as string]: i }}>
          <button type="button" className={seleccionado === l.indicador ? "activo" : ""} aria-pressed={seleccionado === l.indicador} onClick={() => alElegir(l.indicador)}>
            <span className="v-nombre">{nombreIndicador(l.indicador, tm)}</span>
            <span className="v-valor">{num(l.valor)} <small>{l.unidad}</small></span>
            <Chispa puntos={series[l.indicador]} nivel={l.nivel} />
            <span className="v-punto" aria-label={t(`common:status.${l.nivel}`)} />
          </button>
        </li>
      ))}
    </ul>
  );
});
