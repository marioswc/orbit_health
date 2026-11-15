import type { Capa } from "./zonas";

/** Flecha con nombre que senala una estructura de la capa de anatomia visible. Coordenadas del dibujo del astronauta. */
export interface Etiqueta {
  texto: string;
  /** Zona a la que pertenece (al acercar solo se muestran las de la zona elegida). */
  zona: string;
  /** Punto de la estructura que senala la flecha. */
  tx: number;
  ty: number;
  /** Donde nace la flecha cuando se ve el cuerpo completo. */
  lx: number;
  ly: number;
  lado: "izq" | "der";
}

// Posiciones calculadas sobre la alineacion de cada capa; ajustar aqui si cambia el arte.
// Los textos nacen fuera de la silueta (x=142 a la izquierda, x=316 a la derecha) para no tapar el cuerpo.
const IZQ = 142, DER = 316;
export const ETIQUETAS: Partial<Record<Capa, Etiqueta[]>> = {
  organos: [
    { texto: "Cerebro", zona: "snc", tx: 239, ty: 66, lx: IZQ, ly: 56, lado: "izq" },
    { texto: "Pulmón", zona: "resp", tx: 222, ty: 165, lx: IZQ, ly: 150, lado: "izq" },
    { texto: "Corazón", zona: "cardio", tx: 244, ty: 158, lx: DER, ly: 140, lado: "der" },
    { texto: "Riñones", zona: "metab", tx: 254, ty: 208, lx: DER, ly: 214, lado: "der" },
    { texto: "Vasos", zona: "piernas", tx: 262, ty: 330, lx: DER, ly: 322, lado: "der" },
  ],
  musculo: [
    { texto: "Pectoral", zona: "resp", tx: 222, ty: 146, lx: IZQ, ly: 128, lado: "izq" },
    { texto: "Bíceps", zona: "brazos", tx: 205, ty: 170, lx: IZQ, ly: 178, lado: "izq" },
    { texto: "Deltoides", zona: "brazos", tx: 210, ty: 136, lx: IZQ, ly: 114, lado: "izq" },
    { texto: "Abdominal", zona: "metab", tx: 239, ty: 195, lx: DER, ly: 201, lado: "der" },
    { texto: "Cuádriceps", zona: "piernas", tx: 227, ty: 297, lx: IZQ, ly: 290, lado: "izq" },
    { texto: "Gemelos", zona: "piernas", tx: 267, ty: 388, lx: DER, ly: 382, lado: "der" },
  ],
  hueso: [
    { texto: "Cráneo", zona: "snc", tx: 239, ty: 72, lx: IZQ, ly: 56, lado: "izq" },
    { texto: "Clavícula", zona: "resp", tx: 211, ty: 125, lx: IZQ, ly: 112, lado: "izq" },
    { texto: "Costillas", zona: "resp", tx: 267, ty: 160, lx: DER, ly: 154, lado: "der" },
    { texto: "Pelvis", zona: "metab", tx: 239, ty: 240, lx: DER, ly: 246, lado: "der" },
    { texto: "Fémur", zona: "piernas", tx: 216, ty: 306, lx: IZQ, ly: 312, lado: "izq" },
    { texto: "Tibia", zona: "piernas", tx: 262, ty: 384, lx: DER, ly: 390, lado: "der" },
  ],
};

/** Punto de arranque de la flecha: fijo con el cuerpo completo; junto a la estructura al acercar. */
export function origenEtiqueta(e: Etiqueta, enfocar: boolean): [number, number] {
  if (!enfocar) return [e.lx, e.ly];
  return e.lado === "izq" ? [e.tx - 28, e.ty - 16] : [e.tx + 28, e.ty - 16];
}

/** Angulo (grados) de la flecha, para orientar la punta. */
export function anguloFlecha(e: Etiqueta, enfocar: boolean): number {
  const [ox, oy] = origenEtiqueta(e, enfocar);
  return (Math.atan2(e.ty - oy, e.tx - ox) * 180) / Math.PI;
}
