const NOMBRES: Record<string, string> = {
  spo2: "SpO₂",
  co2: "CO₂ de cabina",
  dosis_pct: "Dosis de radiación",
  avpu: "Conciencia (AVPU)",
  glucosa: "Glucemia",
  frecuencia_cardiaca: "Frecuencia cardíaca",
  frecuencia_respiratoria: "Frecuencia respiratoria",
  presion_sistolica: "Presión sistólica",
  presion_diastolica: "Presión diastólica",
  temperatura: "Temperatura",
  sueno_horas: "Horas de sueño",
};

/** Nombre legible de un indicador; si no esta en la lista, lo humaniza a partir de la clave. */
export function nombreIndicador(clave: string, t?: ((clave: string) => string) | number): string {
  if (NOMBRES[clave]) return typeof t === "function" ? t(`monitor:ind.largo.${clave}`) : NOMBRES[clave];
  const h = clave.replace(/_/g, " ");
  return h.charAt(0).toUpperCase() + h.slice(1);
}

