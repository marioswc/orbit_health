const NOMBRES: Record<string, string> = {
  spo2: "SpO₂",
  frecuencia_respiratoria: "Frec. respiratoria",
  frecuencia_cardiaca: "Frec. cardiaca",
  presion_sistolica: "Presión sistólica",
  presion_diastolica: "Presión diastólica",
  temperatura: "Temperatura",
  avpu: "Conciencia (AVPU)",
};

/** Nombre legible de un indicador del backend (clave en snake_case). */
export function nombreIndicador(clave: string): string {
  if (NOMBRES[clave]) return NOMBRES[clave];
  const t = clave.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}
