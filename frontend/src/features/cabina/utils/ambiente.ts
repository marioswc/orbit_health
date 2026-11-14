import type { Nivel } from "../../../shared/types/nivel";
import type { AlertasColectivas, LecturaAmbiental } from "../types/cabina";

const ORDEN: Record<Nivel, number> = { verde: 0, amarillo: 1, rojo: 2 };

export interface Ambiente {
  co2: number | null;
  co2Nivel: Nivel | null;
  dosis: LecturaAmbiental | null;
  /** Peor nivel conocido entre CO2 y dosis; "sin_datos" si el backend no informo ninguno. */
  nivel: Nivel | "sin_datos";
}

/**
 * Une lo que informa el backend sobre el ambiente de cabina. No calcula niveles: toma los que ya trae la API
 * (los umbrales viven en el backend). El CO2 puede venir del cruce colectivo o de una lectura del tripulante.
 */
export function resolverAmbiente(
  alertas: AlertasColectivas | null,
  co2Local: LecturaAmbiental | null,
  dosis: LecturaAmbiental | null,
): Ambiente {
  const globalCo2 = alertas?.co2_mmhg ?? null;
  const co2 = globalCo2 ?? co2Local?.valor ?? null;
  // El nivel solo se usa si corresponde al mismo valor que se muestra
  const co2Nivel = alertas?.co2_nivel ?? (co2Local && co2Local.valor === co2 ? co2Local.nivel : null);
  const conocidos = [co2Nivel, dosis?.nivel].filter((n): n is Nivel => n != null);
  const nivel = conocidos.length ? conocidos.reduce((p, n) => (ORDEN[n] > ORDEN[p] ? n : p)) : "sin_datos";
  return { co2, co2Nivel, dosis, nivel };
}

export const DESCRIPCION_CO2: Record<Nivel, string> = {
  verde: "Nominal",
  amarillo: "Saturación parcial de filtros",
  rojo: "Riesgo de cefalea o acidosis",
};

