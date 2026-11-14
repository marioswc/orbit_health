import { useCallback, useEffect, useState } from "react";

export type Tema = "light" | "dark";
const CLAVE = "orbit-tema";

function inicial(): Tema {
  const puesto = document.documentElement.dataset.theme;
  if (puesto === "dark" || puesto === "light") return puesto;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Tema claro/oscuro. Se recuerda en localStorage (con try/catch: puede no estar disponible). */
export function useTema() {
  const [tema, setTema] = useState<Tema>(inicial);
  useEffect(() => {
    document.documentElement.dataset.theme = tema;
    try { localStorage.setItem(CLAVE, tema); } catch { /* sin almacenamiento */ }
  }, [tema]);
  const alternar = useCallback(() => {
    const raiz = document.documentElement;
    raiz.classList.add("cambiando-tema");
    window.setTimeout(() => raiz.classList.remove("cambiando-tema"), 450);
    setTema((t) => (t === "dark" ? "light" : "dark"));
  }, []);
  return { tema, alternar };
}
