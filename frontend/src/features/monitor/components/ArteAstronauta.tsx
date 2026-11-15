import type { CSSProperties } from "react";
import { useTranslation } from "../../../i18n";
import type { Capa } from "../zonas";
import astronauta from "../assets/astronauta.svg";
import esqueleto from "../assets/esqueleto.webp";
import musculos from "../assets/musculos.webp";
import organos from "../assets/organos.webp";

// Coordenadas = px del dibujo original del astronauta. Las capas de anatomia se alinean por el centro de la cabeza
// con el casco y por los pies con las botas (ver assets/ATRIBUCION.md).
export const VB = { x: 129.25, y: 21.5, w: 215.25, h: 430.75 };
export const VIEWBOX = `${VB.x} ${VB.y} ${VB.w} ${VB.h}`;

export type Caja = [number, number, number, number]; // x, y, ancho, alto

export const CAJAS: Record<Capa, Caja> = {
  traje: [VB.x, VB.y, VB.w, VB.h],
  musculo: [173.6, 48.4, 132.6, 391],
  hueso: [166.9, 48.9, 144.8, 397.3],
  organos: [155.7, 49.8, 171.9, 396.5],
};

export const URL_CAPA: Record<Capa, string> = { traje: astronauta, musculo: musculos, hueso: esqueleto, organos };
export const CAPAS_ANAT: Exclude<Capa, "traje">[] = ["musculo", "hueso", "organos"];

// Region del cuerpo que se ve a todo color al acercar la camara a una zona (donde estan los organos y musculos)
export const REGIONES: Record<string, Caja[]> = {
  snc: [[205, 40, 70, 80]],
  resp: [[200, 118, 78, 70]],
  cardio: [[214, 124, 58, 56]],
  metab: [[205, 180, 70, 72]],
  brazos: [[118, 108, 92, 236], [268, 108, 92, 236]],
  piernas: [[200, 246, 78, 206]],
};

/** Posicion y tamano de una caja (coords del dibujo) como porcentajes del lienzo. */
export function aPorcentaje(c: Caja): CSSProperties {
  return {
    left: `${((c[0] - VB.x) / VB.w) * 100}%`,
    top: `${((c[1] - VB.y) / VB.h) * 100}%`,
    width: `${(c[2] / VB.w) * 100}%`,
    height: `${(c[3] / VB.h) * 100}%`,
  };
}

/** Una region (coords del dibujo) como fracciones de la caja de su capa. */
export function aFraccion(region: Caja, caja: Caja): Caja {
  return [(region[0] - caja[0]) / caja[2], (region[1] - caja[1]) / caja[3], region[2] / caja[2], region[3] / caja[3]];
}

/** Mascara radial suave sobre la(s) region(es) de la zona (estatica: no se vuelve a pintar al mover la camara). */
export function mascara(regiones: Caja[], caja: Caja): CSSProperties {
  if (regiones.length === 0) return {};
  const m = regiones.map((r) => {
    const [x, y, w, h] = aFraccion(r, caja);
    const f = (n: number) => (n * 100).toFixed(1);
    return `radial-gradient(ellipse ${f((w / 2) * 1.12)}% ${f((h / 2) * 1.12)}% at ${f(x + w / 2)}% ${f(y + h / 2)}%, #000 50%, transparent 100%)`;
  }).join(", ");
  return { maskImage: m, WebkitMaskImage: m } as CSSProperties;
}

/** Descarga una capa en segundo plano para que aparezca al instante cuando se pida. */
export function precargar(capa: Capa) {
  if (typeof Image === "undefined") return;
  const img = new Image();
  img.decoding = "async";
  img.src = URL_CAPA[capa];
}

interface Props {
  capa: Capa;
  meses: number;
  zona: string;
  /** true al acercar la camara: solo la region de la zona elegida queda a color. */
  enfocar: boolean;
  /** Capas que ya se pidieron alguna vez: las demas no se descargan ni se pintan. */
  visitadas: ReadonlySet<Capa>;
}

/**
 * Capas del cuerpo como <img> (se componen en la GPU, mucho mas barato que SVG con mascaras).
 * El traje es la base; la capa de anatomia activa se ve completa y, al acercar, solo su region a color.
 */
export function Capas({ capa, meses, zona, enfocar, visitadas }: Props) {
  const { t } = useTranslation("monitor");
  const regiones = REGIONES[zona] ?? [];
  return (
    <>
      <img className="capa-traje" src={URL_CAPA.traje} alt={t("figura.altTraje")} draggable={false}
        decoding="async" {...{ fetchpriority: "high" }} style={{ ...aPorcentaje(CAJAS.traje), opacity: capa === "traje" ? 1 : 0.16 }} />

      {CAPAS_ANAT.filter((c) => visitadas.has(c) || c === capa).map((c) => {
        const activa = capa === c;
        // con mas meses en microgravedad el hueso se ve menos denso (metafora visual)
        const opacidad = activa ? (c === "hueso" ? 1 - (meses / 6) * 0.5 : 1) : 0;
        return (
          <div key={c} className="capa-grupo" style={{ ...aPorcentaje(CAJAS[c]), opacity: opacidad }} aria-hidden={!activa}>
            {activa && enfocar && <img className="anat-apagada" src={URL_CAPA[c]} alt="" draggable={false} decoding="async" />}
            <img className="anat-viva" src={URL_CAPA[c]} alt="" draggable={false} decoding="async"
              style={activa && enfocar ? mascara(regiones, CAJAS[c]) : undefined} />
          </div>
        );
      })}
    </>
  );
}
