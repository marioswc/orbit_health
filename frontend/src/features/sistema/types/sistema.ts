/** GET /api/salud */
export interface Salud {
  base_ok: boolean; detalle: string;
  arranque?: { estado: string; detalle?: string };
  respaldos: number; ultimo_respaldo: string | null; respaldo_cada_min: number;
}
/** GET /api/auditoria (requiere medico o comandante si la autenticacion esta activa) */
export interface EventoAuditoria { id: number; actor: string; accion: string; payload: string; ts: string }
/** GET /api/auditoria/verificar */
export interface VerificacionAuditoria { valida: boolean; total: number; primer_invalido: number | null }
