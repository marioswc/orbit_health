import { useEffect, useState } from "react";
import { translate } from "../../i18n";
import { MIN_MS, usePendiente } from "../../i18n/cambio";

/** Icono de traductor: una "A" y un caracter de otro alfabeto. */
const IconoTraductor = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 6h8M8 4v2M10.5 6c-.6 3.2-2.6 5.6-5.5 7" />
    <path d="M5.5 8.5c1 1.8 2.6 3.3 5 4.3" />
    <path d="m12.5 20 3.8-9 3.7 9M13.9 17h4.8" />
  </svg>
);

/**
 * Modal "Cambiando a…" mientras se traduce la interfaz: icono de traductor y barra de avance con porcentaje.
 * El avance se calcula con el reloj (no con una animacion CSS) para que se vea tambien con "reducir movimiento" y en equipos modestos.
 */
export default function CambioIdioma() {
  const destino = usePendiente();
  const [p, setP] = useState(0);
  useEffect(() => {
    if (!destino) { setP(0); return; }
    const ini = performance.now();
    let raf = 0;
    const paso = (t: number) => {
      const x = Math.min(1, (t - ini) / MIN_MS);
      setP(1 - (1 - x) * (1 - x)); // rapido al inicio, frena al final
      if (x < 1) raf = requestAnimationFrame(paso);
    };
    raf = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(raf);
  }, [destino]);
  if (!destino) return null;
  const pct = Math.round(p * 100);
  return (
    <div className="cambio-idioma" role="status" aria-live="polite" aria-busy="true">
      <div className="cambio-tarjeta">
        <span className="cambio-icono"><IconoTraductor /></span>
        <strong>{translate(destino, "common", "language.switching", { idioma: translate(destino, "common", `language.${destino}`) })}</strong>
        <span className="suave">{translate(destino, "common", "language.hint")}</span>
        <div className="cambio-progreso">
          <span className="cambio-barra" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={translate(destino, "common", "language.hint")}>
            <span className="cambio-relleno" style={{ transform: `scaleX(${p})` }} />
          </span>
          <span className="cambio-pct">{pct} %</span>
        </div>
      </div>
    </div>
  );
}
