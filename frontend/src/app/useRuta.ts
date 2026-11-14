import { useCallback, useEffect, useState } from "react";
import { VISTAS, type Vista } from "./BarraLateral";

const IDS = VISTAS.map((v) => v.id) as string[];

/** Vista a partir de la URL: #/historial (ruta) o ?vista=historial (compatibilidad con enlaces de ensayo). */
export function vistaDeUrl(loc: { hash: string; search: string }): Vista {
  const deHash = loc.hash.replace(/^#\/?/, "").split(/[/?]/)[0];
  const deQuery = new URLSearchParams(loc.search).get("vista") ?? "";
  const v = deHash || deQuery;
  return (IDS.includes(v) ? v : "monitor") as Vista;
}

/**
 * Ruta de cada pestana en el hash (#/monitor, #/historial, ...): funciona sin servidor ni internet, con enlaces
 * compartibles y botones Atras/Adelante del navegador. Cambiar de vista agrega una entrada al historial.
 */
export function useRuta(): [Vista, (v: Vista) => void] {
  const [vista, setVista] = useState<Vista>(() => vistaDeUrl(window.location));

  useEffect(() => {
    const alCambiar = () => setVista(vistaDeUrl(window.location));
    window.addEventListener("hashchange", alCambiar);
    window.addEventListener("popstate", alCambiar);
    return () => { window.removeEventListener("hashchange", alCambiar); window.removeEventListener("popstate", alCambiar); };
  }, []);

  const ir = useCallback((v: Vista) => {
    if (window.location.hash === `#/${v}`) return;
    window.location.hash = `/${v}`; // dispara hashchange y deja la entrada en el historial
  }, []);

  useEffect(() => {
    const etiqueta = VISTAS.find((x) => x.id === vista)?.etiqueta;
    document.title = etiqueta ? `${etiqueta} · ORBIT Health` : "ORBIT Health";
  }, [vista]);

  return [vista, ir];
}
