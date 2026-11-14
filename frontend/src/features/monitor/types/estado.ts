import type { Nivel } from "../../../shared/types/nivel";

export interface LecturaEstado { indicador: string; valor: number; unidad: string; nivel: Nivel; ts: string }
export interface Estado {
  indicadores: LecturaEstado[];
  news2: { puntos: number; nivel: Nivel; faltantes: string[] };
  nivel_general: Nivel;
  ventana_min: number;
}
