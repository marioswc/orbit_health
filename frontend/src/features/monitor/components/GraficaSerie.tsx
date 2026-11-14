import { memo } from "react";
import type { SerieHistorial } from "../types/estado";

interface Props {
  serie: SerieHistorial | null;
  cargando: boolean;
  error: string;
  alCerrar: () => void;
}

const W = 420;
const H = 120;
const PAD = 12;

/** Minigrafica SVG de la serie temporal de un indicador (acromatica + foco HUD). */
function GraficaSerie({ serie, cargando, error, alCerrar }: Props) {
  if (!serie && !cargando && !error) return null;

  const puntos = serie?.puntos ?? [];
  const valores = puntos.map((p) => p.valor);
  const min = valores.length ? Math.min(...valores) : 0;
  const max = valores.length ? Math.max(...valores) : 1;
  const rango = max - min || 1;

  const coords = puntos.map((p, idx) => {
    const x = puntos.length === 1 ? W / 2 : PAD + (idx / (puntos.length - 1)) * (W - PAD * 2);
    const y = H - PAD - ((p.valor - min) / rango) * (H - PAD * 2);
    return { x: Number(x.toFixed(1)), y: Number(y.toFixed(1)), p };
  });
  const d = coords.map((c, idx) => `${idx === 0 ? "M" : "L"}${c.x} ${c.y}`).join(" ");

  return (
    <section className="tarjeta grafica-serie" aria-label="Historial del indicador">
      <div className="grafica-cab">
        <div>
          <h2>{serie ? `${serie.etiqueta} · últimos ${serie.dias} días` : "Historial"}</h2>
          {serie && (
            <p className="suave">
              {serie.resumen.n} {serie.resumen.n === 1 ? "lectura" : "lecturas"}
              {serie.resumen.n > 0 && ` · mín ${serie.resumen.min} · media ${serie.resumen.media} · máx ${serie.resumen.max} ${serie.unidad}`}
            </p>
          )}
        </div>
        <button type="button" className="ghost" onClick={alCerrar}>Cerrar</button>
      </div>

      {cargando && <span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}
      {error && <p className="error">{error}</p>}
      {!cargando && !error && serie && puntos.length === 0 && (
        <p className="suave">Sin lecturas en este periodo.</p>
      )}
      {!cargando && !error && puntos.length > 0 && (
        <svg className="serie-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Serie de ${serie?.etiqueta ?? "indicador"} con ${puntos.length} puntos`}>
          <line className="serie-eje" x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} />
          {coords.length > 1 && <path className="serie-linea" d={d} fill="none" />}
          {coords.map((c, i) => (
            <circle key={`${c.p.ts}-${i}`} className={`serie-punto ${c.p.nivel}`} cx={c.x} cy={c.y} r={coords.length > 40 ? 2.2 : 3.4}>
              <title>{`${c.p.valor} ${serie?.unidad ?? ""} (${c.p.nivel}) · ${c.p.ts.slice(0, 16).replace("T", " ")}`}</title>
            </circle>
          ))}
        </svg>
      )}
    </section>
  );
}

export default memo(GraficaSerie);

