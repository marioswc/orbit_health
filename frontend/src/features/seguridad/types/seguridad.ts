export interface AuthEstado { activa: boolean; sesion_horas: number }

export interface Actor {
  tripulante_id: string | null;
  nombre?: string;
  rol: string;
}

export interface LoginRespuesta {
  token: string;
  expira_ts: string;
  tripulante_id: string;
  rol: string;
}

