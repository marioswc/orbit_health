import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { PuntoHistorial, SerieHistorial } from "../types/estado";

/**
 * Series de 14 dias (GET /api/historial) de varios indicadores, pedidas de una en una para no saturar el servidor.
 * Cada serie aparece en cuanto llega; si una falla se omite (la consola sigue mostrando el valor actual).
 */
export function useSeries(tid: string, claves: string[], limite = 30): Record<string, PuntoHistorial[]> {
  const [series, setSeries] = useState<Record<string, PuntoHistorial[]>>({});
  const llave = claves.join("|");
  useEffect(() => {
    let cancelado = false;
    setSeries({});
    (async () => {
      for (const c of claves) {
        if (cancelado || !tid) return;
        try {
          const d = await api<SerieHistorial>(`/historial/${tid}?indicador=${encodeURIComponent(c)}&dias=14&limite=${limite}`);
          if (!cancelado) setSeries((s) => ({ ...s, [c]: d.puntos }));
        } catch { /* sin serie para este indicador */ }
      }
    })();
    return () => { cancelado = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tid, llave, limite]);
  return series;
}
