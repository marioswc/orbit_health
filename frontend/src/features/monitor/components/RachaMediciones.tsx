import { useState } from "react";
import { useRecargaPorClave } from "../../../shared/hooks/useRecargaPorClave";
import { api } from "../../../shared/api/client";
import type { Estado } from "../types/estado";

interface LogroRacha { id: string; nombre: string; logrado: boolean }

interface DatosRacha {
  racha_dias: number;
  mejor_racha_dias: number;
  dias_completos: number;
  hoy_completo: boolean;
  hoy_faltan: string[];
  logros: LogroRacha[];
  regla: string;
}

interface Props {
  tripulanteId: string;
  estado: Estado | null;
}

/** Racha de días con los 5 signos vitales registrados y logros ligeros, sin presión. */
export default function RachaMediciones({ tripulanteId, estado }: Props) {
  const [racha, setRacha] = useState<DatosRacha | null>(null);

  useRecargaPorClave(() => {
    if (!tripulanteId) return;
    let activo = true;
    api<DatosRacha>(`/racha/${encodeURIComponent(tripulanteId)}`)
      .then((d) => { if (activo) setRacha(d); })
      .catch(() => { if (activo) setRacha(null); });
    return () => { activo = false; };
  }, estado, [tripulanteId]);

  if (!racha) return null;

  return (
    <section className="tarjeta racha-bloque" aria-label="Racha de mediciones">
      <div className="racha-cab">
        <div>
          <h2>Constancia de mediciones</h2>
          <p className="suave">{racha.regla}</p>
        </div>
        <div className="racha-nums">
          <span className="badge verde">{racha.racha_dias} {racha.racha_dias === 1 ? "día" : "días"} seguidos</span>
          <span className="suave">Mejor: {racha.mejor_racha_dias} · Días completos: {racha.dias_completos}</span>
        </div>
      </div>

      <p className="racha-hoy">
        {racha.hoy_completo
          ? "Hoy: 5 de 5 signos vitales completos."
          : `Hoy faltan: ${racha.hoy_faltan.join(", ")}.`}
      </p>

      <div className="racha-logros">
        {racha.logros.map((l) => (
          <span key={l.id} className={`badge ${l.logrado ? "verde" : "sin_datos"}`}>
            {l.logrado ? "✓ " : ""}{l.nombre}
          </span>
        ))}
      </div>
    </section>
  );
}

