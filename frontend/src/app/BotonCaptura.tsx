interface Props {
  alAbrir: () => void;
  /** Sin tripulante elegido no hay a quién registrarle una medición. */
  disponible: boolean;
}

/** Botón flotante (abajo a la derecha) para abrir la captura manual desde cualquier vista. */
export default function BotonCaptura({ alAbrir, disponible }: Props) {
  return (
    <button type="button" className="btn-primario fab" onClick={alAbrir} disabled={!disponible} aria-label="Captura manual" title="Captura manual">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
      <span className="fab-texto">Captura manual</span>
    </button>
  );
}
