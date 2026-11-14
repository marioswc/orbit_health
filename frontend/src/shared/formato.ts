/** Valor listo para mostrar: como maximo 2 decimales y sin ceros sobrantes (evita 37.599999999999994; 37.60 se ve 37.6). */
export const num = (v: number): number => Number(v.toFixed(2));
