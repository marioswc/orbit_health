import { useCallback, useEffect, useState } from "react";

/** Seccion (pestana) a partir del hash: #/bienestar/diario -> "diario". Si no es valida, la de por defecto. */
export function seccionDeUrl(hash: string, vista: string, validas: readonly string[], porDefecto: string): string {
  const [v, s] = hash.replace(/^#\/?/, "").split("?")[0].split("/");
  return v === vista && s && validas.includes(s) ? s : porDefecto;
}

/**
 * Pestana activa guardada en la ruta (#/bienestar/diario): enlaces compartibles, Atras/Adelante del navegador y recarga sin perder
 * la seccion. Funciona sin servidor. Cambiar de pestana agrega una entrada al historial.
 */
export function useSeccion<T extends string>(vista: string, validas: readonly T[], porDefecto: T): [T, (s: T) => void] {
  const [seccion, setSeccion] = useState<string>(() => seccionDeUrl(window.location.hash, vista, validas, porDefecto));

  useEffect(() => {
    const alCambiar = () => {
      // solo reacciona mientras esta pantalla es la vista activa
      if (window.location.hash.replace(/^#\/?/, "").split(/[/?]/)[0] === vista) setSeccion(seccionDeUrl(window.location.hash, vista, validas, porDefecto));
    };
    window.addEventListener("hashchange", alCambiar);
    window.addEventListener("popstate", alCambiar);
    return () => { window.removeEventListener("hashchange", alCambiar); window.removeEventListener("popstate", alCambiar); };
  }, [vista, validas, porDefecto]);

  const ir = useCallback((s: T) => {
    setSeccion(s);
    const destino = `#/${vista}/${s}`;
    if (window.location.hash !== destino) window.location.hash = destino.slice(1);
  }, [vista]);

  return [seccion as T, ir];
}
