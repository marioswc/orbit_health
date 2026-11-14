import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { SerieHistorial } from "../types/estado";

/** Carga la serie temporal de un indicador para la grafica de tendencia. */
export function useHistorialIndicador(tid: string, indicador: string | null) {
  const [serie, setSerie] = useState<SerieHistorial | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!tid || !indicador) { setSerie(null); setError(""); return; }
    let cancelado = false;
    setCargando(true);
    setError("");
    api<SerieHistorial>(`/historial/${tid}?indicador=${encodeURIComponent(indicador)}&dias=14&limite=120`)
      .then((d) => { if (!cancelado) setSerie(d); })
      .catch((e) => { if (!cancelado) setError((e as Error).message); })
      .finally(() => { if (!cancelado) setCargando(false); });
    return () => { cancelado = true; };
  }, [tid, indicador]);

  return { serie, cargando, error };
}

