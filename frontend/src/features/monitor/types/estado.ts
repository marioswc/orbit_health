import type { Nivel } from "../../../shared/types/nivel";

/** Comparacion con la linea base personal (movil), calculada por el backend. `aplica` es false si hay pocas muestras. */
export interface LineaBase { aplica: boolean; n: number; aviso: boolean; media?: number; desviacion?: number; z?: number | null }

export interface LecturaEstado { indicador: string; valor: number; unidad: string; nivel: Nivel; ts: string; linea_base?: LineaBase }
export interface ReglaCombinada { id: string; nombre: string; nivel: Nivel }

export interface PeligroRelacionado { id: string; nombre: string; url: string }
export interface EstiloAsistente { tono: string; detalle: string; recordatorios: string }

export interface Estado {
  indicadores: LecturaEstado[];
  news2: { puntos: number; nivel: Nivel; faltantes: string[] };
  peligros_relacionados?: PeligroRelacionado[];
  reglas_combinadas?: ReglaCombinada[];
  nivel_general: Nivel;
  nivel_fisiologico?: Nivel;
  ventana_min: number;
  proxima_captura_min?: number;
  acciones_sugeridas?: string[];
  estilo?: EstiloAsistente;
}

export interface ExplicacionIndicador {
  que_es: string;
  por_que_se_mide: string;
  como_medirlo: string;
  en_el_espacio: string;
  cuando_avisar: string;
  fuentes: string[];
}

export interface ExplicacionesCatalogo {
  estado: string;
  aviso: string;
  explicaciones: Record<string, ExplicacionIndicador>;
}

export interface PeligroHRP {
  nombre: string;
  nombre_oficial: string;
  url: string;
  resumen: string;
  como_responde_orbit: string;
}

export interface RiesgoHRP {
  nombre_oficial: string;
  url: string;
  cobertura: "cubierto" | "parcial" | "no_cubierto";
  indicadores: string[];
  nota: string;
}

export interface PeligrosCatalogo {
  estado: string;
  fuentes: { peligros: string; riesgos: string };
  peligros: Record<string, PeligroHRP>;
  indicadores_por_peligro: Record<string, string[]>;
  riesgos: RiesgoHRP[];
  resumen_cobertura: { total: number; cubierto: number; parcial: number; no_cubierto: number };
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
