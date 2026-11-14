import { memo } from "react";
import type { Nivel } from "../../../shared/types/nivel";
import type { LecturaEstado } from "../types/estado";

type NivelZona = Nivel | "sin_datos";

const ZONAS: { id: string; etiqueta: string; indicadores: string[] }[] = [
  { id: "snc", etiqueta: "Cabeza / SNC", indicadores: ["avpu"] },
  { id: "cardio", etiqueta: "Cardiovascular", indicadores: ["presion_sistolica", "presion_diastolica", "frecuencia_cardiaca"] },
  { id: "resp", etiqueta: "Respiratorio", indicadores: ["spo2", "frecuencia_respiratoria"] },
  { id: "metab", etiqueta: "Tronco / Metabólico", indicadores: ["glucosa", "temperatura"] },
  { id: "extr", etiqueta: "Extremidades", indicadores: [] }, // sin indicador en el prototipo
];
const ORDEN: Record<Nivel, number> = { verde: 0, amarillo: 1, rojo: 2 };

function nivelZona(indicadores: string[], lecturas: LecturaEstado[]): NivelZona {
  const dentro = lecturas.filter((l) => indicadores.includes(l.indicador));
  if (dentro.length === 0) return "sin_datos";
  return dentro.reduce<Nivel>((peor, l) => (ORDEN[l.nivel] > ORDEN[peor] ? l.nivel : peor), "verde");
}

function FiguraHumana({ lecturas }: { lecturas: LecturaEstado[] }) {
  const n = Object.fromEntries(ZONAS.map((z) => [z.id, nivelZona(z.indicadores, lecturas)])) as Record<string, NivelZona>;
  return (
    <section className="panel">
      <h2>Estado por zona</h2>
      <div className="fila">
        <svg viewBox="0 0 120 260" width="150" role="img" aria-label="Mapa anatómico de estado">
          <circle className={`zona ${n.snc}`} cx="60" cy="25" r="20" />
          <rect className={`zona ${n.cardio}`} x="38" y="50" width="44" height="34" rx="10" />
          <rect className={`zona ${n.resp}`} x="38" y="88" width="44" height="34" rx="10" />
          <rect className={`zona ${n.metab}`} x="42" y="126" width="36" height="46" rx="10" />
          <rect className={`zona ${n.extr}`} x="42" y="176" width="14" height="70" rx="6" />
          <rect className={`zona ${n.extr}`} x="64" y="176" width="14" height="70" rx="6" />
        </svg>
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {ZONAS.map((z) => (
            <li key={z.id} style={{ marginBottom: 6 }}>
              <span className={`badge ${n[z.id]}`}>{n[z.id] === "sin_datos" ? "sin datos" : n[z.id]}</span>{" "}
              {z.etiqueta}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default memo(FiguraHumana);
