import { useCallback, useEffect, useState } from "react";
import { api, getToken, onNoAutorizado, post, setToken } from "../../../shared/api/client";
import type { Actor, AuthEstado, LoginRespuesta } from "../types/seguridad";

/**
 * Estado de autenticacion a bordo.
 * Si el backend tiene ORBIT_AUTH=0 (`activa: false`), no bloquea la aplicacion.
 */
export function useAuth() {
  const [activa, setActiva] = useState<boolean | null>(null);
  const [actor, setActor] = useState<Actor | null>(null);

  const verificar = useCallback(async () => {
    try {
      const e = await api<AuthEstado>("/auth/estado");
      setActiva(e.activa);
      if (!e.activa) { setActor(null); return; }
      if (!getToken()) { setActor(null); return; }
      const yo = await api<Actor>("/auth/yo");
      setActor(yo.tripulante_id ? yo : null);
    } catch {
      // Si el endpoint no responde, no asumimos autenticacion activa para no bloquear tests ni modo demo
      setActiva((prev) => prev ?? false);
      setActor(null);
    }
  }, []);

  useEffect(() => {
    verificar();
    onNoAutorizado(() => {
      setToken(null);
      setActor(null);
    });
    return () => onNoAutorizado(null);
  }, [verificar]);

  async function login(tripulanteId: string, pin: string) {
    const r = await post<LoginRespuesta>("/auth/login", { tripulante_id: tripulanteId, pin });
    setToken(r.token);
    setActor({ tripulante_id: r.tripulante_id, rol: r.rol });
    return r;
  }

  async function recuperar(tripulanteId: string, codigoRecuperacion: string, pinNuevo: string) {
    await post("/auth/recuperar", {
      tripulante_id: tripulanteId,
      codigo_recuperacion: codigoRecuperacion,
      pin_nuevo: pinNuevo,
    });
  }

  async function logout() {
    try { await post("/auth/logout", {}); } catch { /* cerrar sesion local de todos modos */ }
    setToken(null);
    setActor(null);
  }

  return { activa, actor, login, recuperar, logout, requiereAcceso: activa === true && !actor };
}

