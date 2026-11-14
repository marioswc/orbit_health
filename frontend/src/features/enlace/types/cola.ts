export interface ItemCola {
  id: number; tripulante_id: string; tipo_evento: string; prioridad: 1 | 2 | 3;
  estado: "retenido" | "en_transito" | "recibido"; hash: string;
}
export interface Cola {
  enlace: { activo: boolean; entorno: string };
  resumen: Record<string, Record<string, number>>;
  items: ItemCola[];
}
