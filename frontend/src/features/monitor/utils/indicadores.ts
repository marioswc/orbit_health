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
export function nombreIndicador(clave: string): string {
  if (NOMBRES[clave]) return NOMBRES[clave];
  const t = clave.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

