import type { Nivel } from "../../../shared/types/nivel";

export interface IndicadorDef { clave: string; etiqueta: string; unidad: string; min: number; max: number }
export interface RespuestaLectura {
  lectura_id: number; nivel: Nivel; puntos_news2: number; observacion: boolean;
  aviso_linea_base: boolean; faltantes_news2: string[]; prioridad: number;
}
