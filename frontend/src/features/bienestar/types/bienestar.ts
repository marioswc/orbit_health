export interface Capsula { id: string; titulo: string; contenido_markdown: string }
export interface RespuestaTamizaje { total: number; positivo: boolean; capsulas: Capsula[] }
export interface NotaDiario { id: number; titulo: string | null; contenido: string; ts: string }
export interface PuntoAnimo { valor: number; ts: string }
/** GET /api/animo/{tid}?dias=N */
export interface SerieAnimo { puntos: PuntoAnimo[]; media: number | null; privado: boolean }
/** POST /api/animo (valor 1 a 5). Privado: nunca se transmite. */
export interface RespuestaAnimo { valor: number; bajo: boolean; aviso_linea_base: boolean; capsulas: Capsula[]; privado?: boolean; transmitido_tierra?: boolean }
