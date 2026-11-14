import { translate } from "../../i18n";
import { MIN_MS, usePendiente } from "../../i18n/cambio";

/** Icono de traductor: una "A" y un caracter de otro alfabeto con flechas de intercambio. */
const IconoTraductor = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 6h8M8 4v2M10.5 6c-.6 3.2-2.6 5.6-5.5 7" />
    <path d="M5.5 8.5c1 1.8 2.6 3.3 5 4.3" />
    <path d="m12.5 20 3.8-9 3.7 9M13.9 17h4.8" />
  </svg>
);

/** Modal "Cambiando a…" mientras se traduce la interfaz: icono de traductor y barra de avance. El texto va en el idioma de destino. */
export default function CambioIdioma() {
  const destino = usePendiente();
  if (!destino) return null;
  return (
    <div className="cambio-idioma" role="status" aria-live="polite" aria-busy="true">
      <div className="cambio-tarjeta">
        <span className="cambio-icono"><IconoTraductor /></span>
        <strong>{translate(destino, "common", "language.switching", { idioma: translate(destino, "common", `language.${destino}`) })}</strong>
        <span className="suave">{translate(destino, "common", "language.hint")}</span>
        <span className="cambio-barra" aria-hidden="true"><span className="cambio-relleno" style={{ ["--dur" as string]: `${MIN_MS}ms` }} /></span>
      </div>
    </div>
  );
}
