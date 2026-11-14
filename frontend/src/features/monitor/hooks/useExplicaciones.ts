import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";

export interface Explicacion {
  que_es: string; por_que_se_mide: string; como_medirlo: string; en_el_espacio: string; cuando_avisar: string; fuentes: string[];
}
interface Respuesta { estado: string; aviso: string; explicaciones: Record<string, Explicacion> }

let cache: Promise<Respuesta> | null = null; // una sola descarga por sesion; se reintenta si falla

/** Explicaciones por indicador (GET /api/explicaciones). Solo descarga cuando `activo`. */
export function useExplicaciones(activo: boolean) {
  const [datos, setDatos] = useState<Respuesta | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!activo) return;
    cache ??= api<Respuesta>("/explicaciones");
    cache.then(setDatos).catch((e) => { cache = null; setError(e.message); });
  }, [activo]);
  return { datos, error };
}
