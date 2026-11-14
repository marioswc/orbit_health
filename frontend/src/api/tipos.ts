export type Nivel = "verde" | "amarillo" | "rojo";

export interface Tripulante { id: string; nombre: string; rol: string }
export interface IndicadorDef { clave: string; etiqueta: string; unidad: string; min: number; max: number }
export interface LecturaEstado { indicador: string; valor: number; unidad: string; nivel: Nivel; ts: string }
export interface Estado {
  indicadores: LecturaEstado[];
  news2: { puntos: number; nivel: Nivel; faltantes: string[] };
  nivel_general: Nivel;
  ventana_min: number;
}
export interface RespuestaLectura {
  lectura_id: number; nivel: Nivel; puntos_news2: number; observacion: boolean;
  aviso_linea_base: boolean; faltantes_news2: string[]; prioridad: number;
}
export interface ItemCola {
  id: number; tripulante_id: string; tipo_evento: string; prioridad: 1 | 2 | 3;
  estado: "retenido" | "en_transito" | "recibido"; hash: string;
}
export interface Cola {
  enlace: { activo: boolean; entorno: string };
  resumen: Record<string, Record<string, number>>;
  items: ItemCola[];
}
export interface Capsula { id: string; titulo: string; contenido_markdown: string }
export interface RespuestaTamizaje { total: number; positivo: boolean; capsulas: Capsula[] }
export interface NotaDiario { id: number; titulo: string | null; contenido: string; ts: string }
