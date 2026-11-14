import type { ReactNode } from "react";
import FiguraHumana from "../components/FiguraHumana";
import type { Estado } from "../types/estado";

interface Props {
  estado: Estado | null;
  /** Espacio para acciones de otras features (p. ej. captura de mediciones), compuesto desde app/. */
  children?: ReactNode;
}

export default function MonitorPage({ estado, children }: Props) {
  return (
    <div className="grid">
      <FiguraHumana lecturas={estado?.indicadores ?? []} />
      {children}
      <section className="panel">
        <h2>Resumen</h2>
        <p>NEWS2 (ventana {estado?.ventana_min ?? "–"} min): <strong>{estado?.news2.puntos ?? 0}</strong>{" "}
          <span className={`badge ${estado?.nivel_general ?? "sin_datos"}`}>{estado?.nivel_general ?? "sin datos"}</span></p>
        {estado && estado.news2.faltantes.length > 0 && (
          <p className="suave">Variables NEWS2 sin dato reciente: {estado.news2.faltantes.join(", ")}. El puntaje puede estar subestimado.</p>
        )}
        {estado?.indicadores.map((i) => (
          <div key={i.indicador} className="item">{i.indicador}: {i.valor} {i.unidad} <span className={`badge ${i.nivel}`}>{i.nivel}</span></div>
        ))}
      </section>
    </div>
  );
}
