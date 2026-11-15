const NOMBRES: Record<string, string> = {
  spo2: "SpO₂",
  frecuencia_respiratoria: "Frec. respiratoria",
  frecuencia_cardiaca: "Frec. cardiaca",
  presion_sistolica: "Presión sistólica",
  presion_diastolica: "Presión diastólica",
  temperatura: "Temperatura",
  avpu: "Conciencia (AVPU)",
  o2_cabina: "O₂ de cabina",
  glucosa: "Glucosa",
  co2: "CO₂ de cabina",
  dosis_pct: "Dosis de radiación",
  sueno_horas: "Sueño",
  sueno_eficiencia_pct: "Eficiencia de sueño",
  sueno_despertares_min: "Despertares",
  variabilidad_cardiaca: "Variabilidad (HRV)",
  ejercicio_min: "Ejercicio diario",
};

/** Nombre legible de un indicador del backend (clave en snake_case). */
export function nombreIndicador(clave: string, t?: ((clave: string) => string) | number): string {
  if (NOMBRES[clave]) return typeof t === "function" ? t(`monitor:ind.corto.${clave}`) : NOMBRES[clave];
  const h = clave.replace(/_/g, " ");
  return h.charAt(0).toUpperCase() + h.slice(1);
}
