export interface Capsula { id: string; titulo: string; contenido_markdown: string }
export interface RespuestaTamizaje { total: number; positivo: boolean; capsulas: Capsula[] }
export interface NotaDiario { id: number; titulo: string | null; contenido: string; ts: string }
