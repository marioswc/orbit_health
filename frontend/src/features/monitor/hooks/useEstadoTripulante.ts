import { useCallback, useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { Estado } from "../types/estado";

export function useEstadoTripulante(tid: string) {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState("");

  const refrescar = useCallback(() => {
    if (tid) api<Estado>(`/estado/${tid}`).then(setEstado).catch((e) => setError(e.message));
  }, [tid]);
  useEffect(() => { refrescar(); }, [refrescar]);

  return { estado, error, refrescar };
}
