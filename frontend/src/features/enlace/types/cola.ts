export interface ItemCola {
  id: number;
  tripulante_id: string;
  tipo_evento: string;
  prioridad: 1 | 2 | 3;
  estado: "retenido" | "en_transito" | "recibido";
  hash: string;
  llegada_estimada_ts?: string | null;
  ack_estimado_ts?: string | null;
  confirmado?: boolean;
}

export interface Cola {
  enlace: { activo: boolean; entorno: string };
  resumen: Record<string, Record<string, number>>;
  items: ItemCola[];
}

export interface PerfilEnlace { nombre: string; retardo_s: number }

export interface InfoLatencia {
  enlace: { activo: boolean; entorno: string };
  perfiles: Record<string, PerfilEnlace>;
  factor_aceleracion: number;
  jitter_pct: number;
  retardo_real_s: number;
  retardo_simulado_s: number;
  ida_y_vuelta_real_s: number;
  ida_y_vuelta_simulada_s: number;
  en_transito: number;
  proxima_llegada_ts: string | null;
  estado_modelo: string;
}

export interface EscenarioDemo { id: string; descripcion: string; pasos: number }

export interface PasoComparativa { t_s: number; t_demo_s: number; texto: string }

export interface ComparativaOrbit {
  entorno: string;
  retardo_unidireccional_s: number;
  respuesta_tierra_min: number;
  evento: string;
  tipo: string;
  aviso: string;
  ventana_sin_apoyo_s: number;
  ventana_sin_apoyo_min: number;
  con_orbit: PasoComparativa[];
  sin_orbit: PasoComparativa[];
}
