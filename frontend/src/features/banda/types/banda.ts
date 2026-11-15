/** GET /api/demo/simulacion/estado */
export interface EventoMision { t_min: number; texto: string; ocurrido: boolean }
export interface EstadoSimulacion {
  activa: boolean; finalizada: boolean; guion: string | null; ritmo: number | null; tick_s: number | null; tick: number;
  minuto_mision: number; duracion_min: number; progreso_pct: number;
  eventos: EventoMision[]; hitos: Record<string, unknown>; error: string | null; aviso: string | null;
  inicio_ts: string | null; fin_ts: string | null;
}
/** GET /api/racha/{tid} */
export interface Racha {
  racha_dias: number; mejor_racha_dias: number; dias_completos: number; hoy_completo: boolean; hoy_faltan: string[];
  logros: { id: string; nombre: string; logrado: boolean }[]; regla: string;
}
export const VITALES_DEL_DIA = 5;
