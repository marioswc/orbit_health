import { useCallback, useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { Estado } from "../types/estado";

export interface ExplicacionEstadoIA {
  fuente: "modelo_local" | "reglas_locales";
  modelo: string | null;
  generado_por_ia: boolean;
  aviso?: string;
  descartado_por?: string;
  explicacion: string;
  nivel_general: string;
}

/** Consulta GET /api/estado/{tid}/explicacion (modelo local opcional o respaldo determinista). */
export function useExplicacionEstado(tripulanteId: string, estado: Estado | null) {
  const [datos, setDatos] = useState<ExplicacionEstadoIA | null>(null);
  const [cargando, setCargando] = useState(false);

  const cargar = useCallback(() => {
    if (!tripulanteId) return;
    let activo = true;
    setCargando(true);
    api<ExplicacionEstadoIA>(`/estado/${encodeURIComponent(tripulanteId)}/explicacion`)
      .then((d) => { if (activo) setDatos(d); })
      .catch(() => { if (activo) setDatos(null); })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, [tripulanteId]);

  useEffect(() => {
    return cargar();
  }, [cargar, estado?.nivel_general, estado?.news2?.puntos, estado?.indicadores?.length]);

  return { datos, cargando, recargar: cargar };
}
