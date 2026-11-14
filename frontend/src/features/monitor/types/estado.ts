import type { Nivel } from "../../../shared/types/nivel";

/** Comparacion con la linea base personal (movil), calculada por el backend. `aplica` es false si hay pocas muestras. */
export interface LineaBase { aplica: boolean; n: number; aviso: boolean; media?: number; desviacion?: number; z?: number | null }

export interface LecturaEstado { indicador: string; valor: number; unidad: string; nivel: Nivel; ts: string; linea_base?: LineaBase }
export interface ReglaCombinada { id: string; nombre: string; nivel: Nivel }

export interface Estado {
  indicadores: LecturaEstado[];
  news2: { puntos: number; nivel: Nivel; faltantes: string[] };
  reglas_combinadas?: ReglaCombinada[];
  nivel_general: Nivel;
  nivel_fisiologico?: Nivel;
  ventana_min: number;
  proxima_captura_min?: number;
  acciones_sugeridas?: string[];
}

export interface PuntoHistorial { valor: number; nivel: Nivel; ts: string }

export interface SerieHistorial {
  indicador: string;
  etiqueta: string;
  unidad: string;
  dias: number;
  puntos: PuntoHistorial[];
  resumen: { n: number; min?: number; max?: number; media?: number };
}
