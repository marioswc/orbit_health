import type { Nivel } from "../../../shared/types/nivel";

/** Comparacion con la linea base personal (movil), calculada por el backend. `aplica` es false si hay pocas muestras. */
export interface LineaBase { aplica: boolean; n: number; aviso: boolean; media?: number; desviacion?: number; z?: number | null }

export interface LecturaEstado { indicador: string; valor: number; unidad: string; nivel: Nivel; ts: string; linea_base?: LineaBase }
export interface Estado {
  indicadores: LecturaEstado[];
  news2: { puntos: number; nivel: Nivel; faltantes: string[] };
  nivel_general: Nivel;
  ventana_min: number;
}
