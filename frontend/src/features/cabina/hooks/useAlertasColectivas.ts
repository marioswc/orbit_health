import { useCallback, useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { AlertasColectivas } from "../types/cabina";

/** Cruce de CO2 de cabina con el estado de la tripulacion. Se actualiza al cambiar `clave` y cada 5 s (en pausa con la pestana oculta). */
export function useAlertasColectivas(clave: unknown) {
  const [datos, setDatos] = useState<AlertasColectivas | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(() => {
    api<AlertasColectivas>("/alertas/colectivas").then((d) => { setDatos(d); setError(""); }).catch((e) => setError(e.message));
  }, []);

  useEffect(() => { cargar(); }, [cargar, clave]);
  useEffect(() => {
    const t = setInterval(() => { if (!document.hidden) cargar(); }, 5000);
    const visible = () => { if (!document.hidden) cargar(); };
    document.addEventListener("visibilitychange", visible);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", visible); };
  }, [cargar]);

  return { datos, error };
}

