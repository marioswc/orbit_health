import type { Nivel } from "../../../shared/types/nivel";

export interface AlertaColectiva { id: string; nombre: string; nivel: Nivel; afectados: number; co2_mmhg: number }

/** Respuesta de GET /api/alertas/colectivas. `co2_nivel` es opcional: hoy el backend no lo informa. */
export interface AlertasColectivas {
  alertas: AlertaColectiva[];
  co2_mmhg: number | null;
  co2_nivel?: Nivel | null;
  niveles: Record<string, Nivel>;
}

/** Lectura ambiental ya clasificada por el backend. */
export interface LecturaAmbiental { valor: number; nivel: Nivel }

