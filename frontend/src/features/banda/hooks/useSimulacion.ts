import { useCallback, useEffect, useRef, useState } from "react";
import { api, post } from "../../../shared/api/client";
import { nivelActual } from "../../../shared/rendimiento";
import type { EstadoSimulacion } from "../types/banda";

const SONDEO_MS = { alto: 2000, medio: 3000, bajo: 5000 } as const;

/**
 * Mision simulada en vivo (GET/POST /api/demo/simulacion/*): estado consultado de a una peticion,
 * mas espaciado en equipos modestos. `alTick` se llama en cada consulta mientras la mision esta activa
 * (para refrescar lo que las bandas simuladas van enviando).
 */
export function useSimulacion(alTick?: () => void) {
  const [estado, setEstado] = useState<EstadoSimulacion | null>(null);
  const [error, setError] = useState("");
  const enVuelo = useRef(false);
  const alTickRef = useRef(alTick);
  alTickRef.current = alTick;

  const consultar = useCallback(async () => {
    if (enVuelo.current) return;
    enVuelo.current = true;
    try {
      const e = await api<EstadoSimulacion>("/demo/simulacion/estado");
      setEstado(e); setError("");
      if (e.activa) alTickRef.current?.();
    } catch (err) { setError((err as Error).message); } finally { enVuelo.current = false; }
  }, []);

  const activa = estado?.activa ?? false;
  useEffect(() => { consultar(); }, [consultar]);
  useEffect(() => {
    if (!activa) return;
    const id = setInterval(() => { if (!document.hidden) consultar(); }, SONDEO_MS[nivelActual()]);
    return () => clearInterval(id);
  }, [activa, consultar]);

  const accion = useCallback(async (ruta: string) => {
    try { setEstado(await post<EstadoSimulacion>(ruta, {})); setError(""); } catch (err) { setError((err as Error).message); }
  }, []);
  const iniciar = useCallback(() => accion("/demo/simulacion/iniciar?ritmo=15&tick_s=1&semilla=7"), [accion]);
  const detener = useCallback(() => accion("/demo/simulacion/detener"), [accion]);

  return { estado, error, iniciar, detener };
}
