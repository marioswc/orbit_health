import type { Capa } from "../zonas";
import astronauta from "../assets/astronauta.svg";
import esqueleto from "../assets/esqueleto.svg";
import musculos from "../assets/musculos.svg";
import organos from "../assets/organos.svg";

// Coordenadas = px del dibujo original del astronauta. Las capas de anatomia (SVG) se alinean por el centro de la cabeza
// con el casco y por los pies con las botas (ver assets/ATRIBUCION.md).
export const VIEWBOX = "129.25 21.5 215.25 430.75";
const [VX, VY, VW, VH] = [129.25, 21.5, 215.25, 430.75];
type Caja = [number, number, number, number]; // x, y, ancho, alto
const POS: Record<"esqueleto" | "musculos" | "organos", Caja> = {
  esqueleto: [167.9, 48.9, 171.3, 397.3],
  musculos: [129.25, 21.5, 215.25, 430.75],
  organos: [138.9, 49.8, 172.1, 396.5],
};

// Region del cuerpo que se "enciende" a color al elegir una zona (donde estan los organos y musculos en la anatomia; bordes suavizados)
const REGIONES: Record<string, Caja[]> = {
  snc: [[205, 40, 70, 80]],
  resp: [[200, 118, 78, 70]],
  cardio: [[214, 124, 58, 56]],
  metab: [[205, 180, 70, 72]],
  brazos: [[100, 112, 100, 200], [278, 112, 100, 200]],
  piernas: [[200, 246, 78, 206]],
};

const CAPAS_ANAT: { id: Capa; href: string; caja: Caja }[] = [
  { id: "musculo", href: musculos, caja: POS.musculos },
  { id: "hueso", href: esqueleto, caja: POS.esqueleto },
  { id: "organos", href: organos, caja: POS.organos },
];

/**
 * Capas del cuerpo: traje (astronauta), musculo, hueso y organos. Solo la capa activa es visible; el traje queda tenue.
 * En la capa activa, la region de la zona elegida se ve a todo color y el resto, apagado.
 */
export function Capas({ capa, meses, zona }: { capa: Capa; meses: number; zona: string }) {
  const regiones = REGIONES[zona] ?? [];
  return (
    <g>
      <defs>
        <filter id="borde-suave" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5" /></filter>
        <mask id="mascara-zona" maskUnits="userSpaceOnUse" x="90" y="10" width="300" height="470">
          <g filter="url(#borde-suave)">
            {regiones.map((r, i) => <rect key={i} x={r[0]} y={r[1]} width={r[2]} height={r[3]} fill="#fff" />)}
          </g>
        </mask>
      </defs>

      <image className="capa-img" href={astronauta} x={VX} y={VY} width={VW} height={VH} preserveAspectRatio="none" style={{ opacity: capa === "traje" ? 1 : 0.16 }} />

      {CAPAS_ANAT.map((c) => {
        // con mas meses en microgravedad el hueso se ve menos denso (metafora visual)
        const visible = capa === c.id ? (c.id === "hueso" ? 1 - (meses / 6) * 0.5 : 1) : 0;
        return (
          <g key={c.id} className="capa-img" style={{ opacity: visible }}>
            <image className="anat-apagada" href={c.href} x={c.caja[0]} y={c.caja[1]} width={c.caja[2]} height={c.caja[3]} preserveAspectRatio="none" />
            <image className="anat-viva" href={c.href} x={c.caja[0]} y={c.caja[1]} width={c.caja[2]} height={c.caja[3]} preserveAspectRatio="none" mask="url(#mascara-zona)" />
          </g>
        );
      })}
    </g>
  );
}
