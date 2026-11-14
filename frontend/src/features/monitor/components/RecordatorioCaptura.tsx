import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import type { Estado } from "../types/estado";

interface RecordatorioTripulante {
  tripulante_id: string;
  nivel_general: string;
  intervalo_min: number;
  vencido: boolean;
  sin_capturas: boolean;
  atrasado_min: number;
  faltan_en_min: number;
  faltantes_news2: string[];
}

interface RecordatoriosEquipo {
  vencidos: number;
  tripulacion: { tripulante_id: string; nombre: string; vencido: boolean; atrasado_min: number }[];
}

interface Props {
  tripulanteId: string;
  estado: Estado | null;
}

/** Aviso de captura vencida o tiempo restante segun nivel actual y preferencias del tripulante. */
export default function RecordatorioCaptura({ tripulanteId, estado }: Props) {
  const [propio, setPropio] = useState<RecordatorioTripulante | null>(null);
  const [equipo, setEquipo] = useState<RecordatoriosEquipo | null>(null);

  useEffect(() => {
    if (!tripulanteId) return;
    let activo = true;
    api<RecordatorioTripulante>(`/recordatorios/${encodeURIComponent(tripulanteId)}`)
      .then((d) => { if (activo) setPropio(d); })
      .catch(() => { if (activo) setPropio(null); });
    api<RecordatoriosEquipo>("/recordatorios")
      .then((d) => { if (activo) setEquipo(d); })
      .catch(() => { if (activo) setEquipo(null); });
    return () => { activo = false; };
  }, [tripulanteId, estado]);

  if (!propio) return null;

  const titulo = propio.sin_capturas
    ? "Sin capturas registradas"
    : propio.vencido
      ? `Captura vencida hace ${propio.atrasado_min} min`
      : `Próxima captura en ${propio.faltan_en_min} min`;

  const resumenEquipo = equipo && equipo.vencidos > 0
    ? ` · Tripulación con captura vencida: ${equipo.vencidos}`
    : "";

  if (propio.vencido || propio.sin_capturas) {
    return (
      <Alerta tono="aviso" titulo={titulo}>
        Intervalo recomendado: cada {propio.intervalo_min} min.
        {propio.faltantes_news2.length > 0 && ` Faltantes NEWS2: ${propio.faltantes_news2.join(", ")}.`}
        {resumenEquipo}
      </Alerta>
    );
  }

  return (
    <section className="tarjeta recordatorio-ok" aria-label="Recordatorio de captura">
      <p className="suave">
        <strong>{titulo}</strong> (intervalo cada {propio.intervalo_min} min){resumenEquipo}
      </p>
    </section>
  );
}

