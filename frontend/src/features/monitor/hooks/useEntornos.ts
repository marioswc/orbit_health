import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";

export interface EntornoMision {
  nombre: string;
  gravedad_g: number | null;
  microgravedad: boolean;
  perfil_enlace_tipico: string[];
  estimacion_osea: { estado: string; nota: string };
}

export interface CatalogoEntornos {
  estado: string;
  fuente_gravedad: string;
  nota_general: string;
  entornos: Record<string, EntornoMision>;
}

let cache: Promise<CatalogoEntornos> | null = null;

/** Catálogo de entornos de misión con su gravedad y aplicabilidad ósea (GET /api/entornos). */
export function useEntornos() {
  const [datos, setDatos] = useState<CatalogoEntornos | null>(null);

  useEffect(() => {
    let activo = true;
    cache ??= api<CatalogoEntornos>("/entornos");
    cache.then((d) => { if (activo) setDatos(d); }).catch(() => { cache = null; });
    return () => { activo = false; };
  }, []);

  return datos;
}

