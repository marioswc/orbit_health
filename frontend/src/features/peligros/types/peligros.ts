export type Cobertura = "cubierto" | "parcial" | "no_cubierto";
export interface Peligro { nombre: string; nombre_oficial: string; url: string; resumen: string; como_responde_orbit: string }
export interface Riesgo { nombre_oficial: string; url: string; cobertura: Cobertura; indicadores: string[]; peligro?: string }
/** GET /api/peligros */
export interface MarcoPeligros {
  estado: string;
  peligros: Record<string, Peligro>;
  riesgos: Riesgo[];
  resumen_cobertura: { total: number; cubierto: number; parcial: number; no_cubierto: number };
}
