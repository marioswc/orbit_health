import { useEffect, useRef, type DependencyList } from "react";

/**
 * Ejecuta `cargar` al montar y cada vez que cambian `deps` o `clave` (p. ej. el estado tras guardar una medicion).
 * La primera llegada de `clave` (de vacia a con valor) no repite la carga inicial: evita pedir dos veces lo mismo al arrancar.
 * `cargar` puede devolver una funcion de limpieza.
 */
export function useRecargaPorClave(cargar: () => void | (() => void), clave: unknown, deps: DependencyList) {
  const previa = useRef<{ deps: DependencyList; vacia: boolean } | null>(null);
  useEffect(() => {
    const p = previa.current;
    const mismasDeps = !!p && p.deps.length === deps.length && p.deps.every((d, i) => Object.is(d, deps[i]));
    const vacia = clave === null || clave === undefined;
    previa.current = { deps, vacia };
    if (p && mismasDeps && p.vacia && !vacia) return; // primera llegada de la clave
    return cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, clave]);
}
