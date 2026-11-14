export interface Capsula { id: string; categoria?: string; titulo: string; contenido_markdown: string }
export interface ContactoProtocolo { rol: string; etiqueta: string }
export interface EstadoCalidadOxigeno {
  presente: boolean;
  valor_pct: number | null;
  nivel: "verde" | "amarillo" | "rojo" | null;
  alerta: boolean;
  causa: "nominal" | "hipoxia_ambiental" | "hiperoxia_riesgo_incendio" | null;
}
export interface ProtocoloCrisis {
  nivel: "ninguno" | "seguimiento" | "crisis";
  titulo: string;
  urgencia: "ninguna" | "preventiva" | "inmediata";
  tono: string;
  pasos: string[];
  calidad_oxigeno?: EstadoCalidadOxigeno;
  contactos_abordo: ContactoProtocolo[];
  permite_aviso_medico: boolean;
  privado: boolean;
  transmitido_tierra: boolean;
  estado_validacion: string;
  aviso: string;
  capsulas?: Capsula[];
}
export interface RespuestaTamizaje {
  tamizaje_id?: number;
  total: number;
  positivo: boolean;
  riesgo_autolesion?: boolean;
  calidad_oxigeno?: EstadoCalidadOxigeno;
  nivel_protocolo?: "ninguno" | "seguimiento" | "crisis";
  protocolo?: ProtocoloCrisis;
  capsulas: Capsula[];
  compartido_medico?: boolean;
  aviso_medico_id?: number | null;
  transmitido_tierra?: boolean;
}
export interface AvisoSaludMental {
  id: number;
  tripulante_id: string;
  tipo: "crisis" | "tamizaje_positivo";
  nivel_protocolo: "seguimiento" | "crisis";
  tamizaje_id: number | null;
  mensaje_opcional: string | null;
  estado: "pendiente" | "atendido" | "revocado";
  atendido_por: string | null;
  creado_ts: string;
}
export interface NotaDiario { id: number; titulo: string | null; contenido: string; ts: string }

/** POST /api/animo (valor 1 a 5). Privado: nunca se transmite. */
export interface RespuestaAnimo { valor: number; bajo: boolean; aviso_linea_base: boolean; capsulas: Capsula[] }
/** GET /api/animo/{tid}?dias=N */
export interface SerieAnimo { puntos: { ts: string; valor: number }[]; media: number | null; privado: boolean }
