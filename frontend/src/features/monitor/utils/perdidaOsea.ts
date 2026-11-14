/** Tasas de perdida de densidad osea en microgravedad (% por mes). Fuente: NASA HRP (video: ~1 %; pagina de gravedad: 1-1.5 %). */
export const TASA_MIN = 1;
export const TASA_MAX = 1.5;
export const MESES_MAX = 6;

export interface RangoPerdida { min: number; max: number }

/** Estimacion simple con tasa constante (calculo del equipo, ilustrativo; no es una prediccion individual). */
export function perdidaOsea(meses: number): RangoPerdida {
  const m = Math.min(Math.max(Math.round(meses), 0), MESES_MAX);
  return { min: m * TASA_MIN, max: m * TASA_MAX };
}

/** Texto para mostrar: "0 %" o "6–9 %". */
export function textoPerdida(meses: number): string {
  const { min, max } = perdidaOsea(meses);
  if (min === 0 && max === 0) return "0 %";
  const f = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  return `${f(min)}–${f(max)} %`;
}
