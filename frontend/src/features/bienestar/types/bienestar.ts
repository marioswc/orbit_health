export interface Capsula { id: string; titulo: string; contenido_markdown: string }
export interface RespuestaTamizaje { total: number; positivo: boolean; capsulas: Capsula[] }
export interface NotaDiario { id: number; titulo: string | null; contenido: string; ts: string }

/** POST /api/animo (valor 1 a 5). Privado: nunca se transmite. */
export interface RespuestaAnimo { valor: number; bajo: boolean; aviso_linea_base: boolean; capsulas: Capsula[] }
/** GET /api/animo/{tid}?dias=N */
export interface SerieAnimo { puntos: { ts: string; valor: number }[]; media: number | null; privado: boolean }
