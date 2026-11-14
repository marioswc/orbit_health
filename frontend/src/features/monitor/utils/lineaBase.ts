import type { LecturaEstado } from "../types/estado";

export type Tendencia = "↑" | "↓" | "→";

export interface ComparacionBase {
  /** Hay linea base suficiente para comparar. */
  disponible: boolean;
  media?: number;
  delta?: number;
  tendencia: Tendencia;
  /** El backend marco un desvio de la linea base (no se recalcula aqui). */
  desvio: boolean;
  muestras: number;
}

/** Compara el valor con la linea base que ya calculo el backend. Solo presenta: no decide niveles. */
export function compararConBase(l: LecturaEstado): ComparacionBase {
  const lb = l.linea_base;
  if (!lb || !lb.aplica || lb.media === undefined) {
    return { disponible: false, tendencia: "→", desvio: false, muestras: lb?.n ?? 0 };
  }
  const delta = l.valor - lb.media;
  // Una diferencia chica frente a la variacion habitual del tripulante se muestra como estable
  const umbral = lb.desviacion && lb.desviacion > 0 ? lb.desviacion * 0.5 : 0;
  const tendencia: Tendencia = Math.abs(delta) <= umbral || delta === 0 ? "→" : delta > 0 ? "↑" : "↓";
  return { disponible: true, media: lb.media, delta, tendencia, desvio: lb.aviso, muestras: lb.n };
}

/** "+20", "-3.5", "0" (un decimal como maximo). */
export function formatoDelta(delta: number): string {
  const n = Number(delta.toFixed(1));
  return `${n > 0 ? "+" : ""}${n}`;
}

