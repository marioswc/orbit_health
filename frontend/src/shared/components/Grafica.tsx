import { Suspense, lazy, useEffect, useState } from "react";
import type { ApexOptions } from "apexcharts";
import { nivelActual } from "../rendimiento";

// ApexCharts se descarga solo cuando hay una grafica en pantalla (no pesa en la carga inicial).
const Chart = lazy(() => import("react-apexcharts"));

export interface Paleta {
  oscuro: boolean;
  ink: string;
  smoke: string;
  stone: string;
  fondo: string;
  hud: string;
  rojo: string;
  amarillo: string;
  verde: string;
}

function leer(): Paleta {
  const cs = getComputedStyle(document.documentElement);
  const g = (n: string, por: string) => cs.getPropertyValue(n).trim() || por;
  return {
    oscuro: document.documentElement.dataset.theme === "dark",
    ink: g("--color-ink", "#000000"),
    smoke: g("--color-smoke", "#777169"),
    stone: g("--color-stone", "#ebe8e4"),
    fondo: g("--color-warm-taupe", "#f5f3f1"),
    hud: g("--hud", "#0447ff"),
    rojo: g("--estado-rojo", "#dc2f1a"),
    amarillo: g("--estado-amarillo", "#d99a00"),
    verde: g("--estado-verde", "#1f9d55"),
  };
}

/** Colores del tema actual (ApexCharts necesita valores concretos, no variables CSS); se actualiza al cambiar claro/oscuro. */
export function usePaleta(): Paleta {
  const [p, setP] = useState<Paleta>(leer);
  useEffect(() => {
    const obs = new MutationObserver(() => setP(leer()));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => obs.disconnect();
  }, []);
  return p;
}

/** Color del semaforo clinico (siempre acompanado de texto en la interfaz). */
export const colorNivel = (p: Paleta, nivel: string) => (nivel === "rojo" ? p.rojo : nivel === "amarillo" ? p.amarillo : nivel === "verde" ? p.verde : p.smoke);

interface Props {
  tipo: "bar" | "area" | "line";
  series: ApexOptions["series"];
  opciones: ApexOptions;
  altura: number | string;
  /** Texto para lectores de pantalla. */
  etiqueta: string;
  className?: string;
  /** Adorno sin informacion propia (p. ej. mini graficas): se oculta a lectores de pantalla. */
  decorativa?: boolean;
}

/** Envoltorio de ApexCharts con el estilo de la plataforma (tema, tipografia, sin barra de herramientas, sin animar en equipos modestos). */
export default function Grafica({ tipo, series, opciones, altura, etiqueta, className, decorativa = false }: Props) {
  const p = usePaleta();
  const anima = nivelActual() === "alto";
  const base: ApexOptions = {
    chart: {
      type: tipo,
      height: altura,
      background: "transparent",
      fontFamily: "inherit",
      foreColor: p.smoke,
      toolbar: { show: false },
      zoom: { enabled: false },
      selection: { enabled: false },
      animations: { enabled: anima, easing: "easeout", speed: 520, animateGradually: { enabled: false }, dynamicAnimation: { speed: 300 } },
    },
    theme: { mode: p.oscuro ? "dark" : "light" },
    grid: { borderColor: p.stone, strokeDashArray: 3, padding: { left: 6, right: 8 } },
    tooltip: { theme: p.oscuro ? "dark" : "light" },
    legend: { show: false },
    dataLabels: { enabled: false },
    states: { hover: { filter: { type: "lighten" } }, active: { filter: { type: "none" } } },
  };
  const mezcla: ApexOptions = {
    ...base,
    ...opciones,
    chart: { ...base.chart, ...opciones.chart },
    grid: { ...base.grid, ...opciones.grid },
    tooltip: { ...base.tooltip, ...opciones.tooltip },
  };
  return (
    <div className={className} {...(decorativa ? { "aria-hidden": true } : { role: "img", "aria-label": etiqueta })}>
      <Suspense fallback={<span className="esqueleto" style={{ height: typeof altura === "number" ? altura : 160, display: "block" }} aria-busy="true" />}>
        <Chart type={tipo} series={series} options={mezcla} height={altura} width="100%" />
      </Suspense>
    </div>
  );
}
