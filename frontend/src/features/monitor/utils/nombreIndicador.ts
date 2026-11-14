const NOMBRES: Record<string, string> = {
  spo2: "SpO₂",
  frecuencia_respiratoria: "Frec. respiratoria",
  frecuencia_cardiaca: "Frec. cardiaca",
  presion_sistolica: "Presión sistólica",
  presion_diastolica: "Presión diastólica",
  temperatura: "Temperatura",
  avpu: "Conciencia (AVPU)",
  o2_cabina: "O₂ de cabina",
};

/** Nombre legible de un indicador del backend (clave en snake_case). */
export function nombreIndicador(clave: string, t?: ((clave: string) => string) | number): string {
  if (NOMBRES[clave]) return typeof t === "function" ? t(`monitor:ind.corto.${clave}`) : NOMBRES[clave];
  const h = clave.replace(/_/g, " ");
  return h.charAt(0).toUpperCase() + h.slice(1);
}
