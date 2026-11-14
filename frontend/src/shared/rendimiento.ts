/**
 * Nivel de rendimiento de la interfaz. Se fija en <html data-rendimiento="..."> y lo leen el CSS (ligero.css)
 * y el fondo de estrellas. Se elige por el equipo y baja solo si se miden fotogramas lentos.
 *
 *  alto  : todo (cristal con desenfoque, animaciones, estrellas con fugaces)
 *  medio : sin desenfoque de fondo ni animaciones infinitas; estrellas a 20 fps, sin fugaces
 *  bajo  : sin animaciones, sin degradados pesados, estrellas estaticas; consultas mas espaciadas
 */
export type Nivel = "alto" | "medio" | "bajo";

export const CLAVE_NIVEL = "orbit-rendimiento";
const ORDEN: Nivel[] = ["alto", "medio", "bajo"];

export interface Entorno {
  /** ?ligero=1|0 o ?rendimiento=alto|medio|bajo */
  forzado?: string | null;
  guardado?: string | null;
  memoriaGb?: number;
  nucleos?: number;
  ahorroDatos?: boolean;
}

const esNivel = (v: unknown): v is Nivel => v === "alto" || v === "medio" || v === "bajo";

/** Decide el nivel inicial. Una orden explicita (URL o guardada) siempre gana. */
export function detectarNivel(e: Entorno): Nivel {
  const f = e.forzado;
  if (f === "1") return "bajo";
  if (f === "0") return "alto";
  if (esNivel(f)) return f;
  if (esNivel(e.guardado)) return e.guardado;
  if (e.ahorroDatos) return "bajo";
  if ((e.memoriaGb !== undefined && e.memoriaGb <= 2) || (e.nucleos !== undefined && e.nucleos <= 2)) return "bajo";
  if ((e.memoriaGb !== undefined && e.memoriaGb <= 4) || (e.nucleos !== undefined && e.nucleos <= 4)) return "medio";
  return "alto";
}

/** Un escalon mas ligero (el "bajo" es el piso). */
export function degradar(n: Nivel): Nivel {
  return ORDEN[Math.min(ORDEN.indexOf(n) + 1, ORDEN.length - 1)];
}

/** Fotogramas lentos: promedio de la ventana por encima del limite (ms) del nivel. */
export const LIMITE_MS: Record<Nivel, number> = { alto: 26, medio: 40, bajo: Infinity };
export const FOTOGRAMAS_VENTANA = 60;

export function debeDegradar(nivel: Nivel, promedioMs: number): boolean {
  return promedioMs > LIMITE_MS[nivel];
}

function leerEntorno(): Entorno {
  const nav = navigator as Navigator & { deviceMemory?: number; connection?: { saveData?: boolean } };
  const q = new URLSearchParams(location.search);
  let guardado: string | null = null;
  try { guardado = localStorage.getItem(CLAVE_NIVEL); } catch { /* sin almacenamiento */ }
  return {
    forzado: q.get("rendimiento") ?? q.get("ligero"), guardado,
    memoriaGb: nav.deviceMemory, nucleos: nav.hardwareConcurrency, ahorroDatos: nav.connection?.saveData === true,
  };
}

export const nivelActual = (): Nivel => {
  const v = document.documentElement.dataset.rendimiento;
  return esNivel(v) ? v : "alto";
};

/** Fija el nivel en <html>. Si `recordar`, lo guarda para la proxima visita (solo cuando se bajo por fotogramas lentos). */
export function aplicarNivel(n: Nivel, recordar = false): void {
  document.documentElement.dataset.rendimiento = n;
  if (recordar) { try { localStorage.setItem(CLAVE_NIVEL, n); } catch { /* sin almacenamiento */ } }
}

export function iniciarRendimiento(): Nivel {
  const e = leerEntorno();
  const n = detectarNivel(e);
  aplicarNivel(n);
  // Una orden en la URL se recuerda ("alto" borra lo guardado), para no repetirla en cada visita
  if (e.forzado !== null && e.forzado !== undefined && (e.forzado === "0" || e.forzado === "1" || esNivel(e.forzado))) {
    try { if (n === "alto") localStorage.removeItem(CLAVE_NIVEL); else localStorage.setItem(CLAVE_NIVEL, n); } catch { /* sin almacenamiento */ }
  }
  return n;
}
