import { useSyncExternalStore } from "react";
import { changeLanguage, getCurrentLanguage, normalizeLanguage, type SupportedLanguage } from "./index";

/**
 * Cambio de idioma con aviso (como el overlay "Cambiando a…" de Trivo): el modal cubre la pantalla, el idioma se aplica
 * detras de el y el modal permanece un minimo para que no sea un parpadeo. Store de modulo: quien dispara (ToggleIdioma)
 * y quien pinta (CambioIdioma, en App) viven en ramas distintas del arbol.
 */
export const MIN_MS = 900;
const APLICAR_MS = 300;

let pendiente: SupportedLanguage | null = null;
const oyentes = new Set<() => void>();
const emitir = () => oyentes.forEach((f) => f());
const dormir = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export const idiomaPendiente = () => pendiente;
export function usePendiente(): SupportedLanguage | null {
  return useSyncExternalStore((f) => { oyentes.add(f); return () => { oyentes.delete(f); }; }, idiomaPendiente, idiomaPendiente);
}

export async function cambiarConAviso(destino: string): Promise<void> {
  const l = normalizeLanguage(destino);
  if (!l || pendiente || l === getCurrentLanguage()) return;
  const reducir = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  pendiente = l;
  emitir();
  try {
    await dormir(reducir ? 80 : APLICAR_MS);
    await changeLanguage(l);
    await dormir(reducir ? 250 : MIN_MS - APLICAR_MS);
  } finally {
    pendiente = null;
    emitir();
  }
}
