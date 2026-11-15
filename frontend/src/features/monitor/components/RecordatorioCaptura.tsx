import { useState } from "react";
import { useRecargaPorClave } from "../../../shared/hooks/useRecargaPorClave";
import { useTranslation } from "../../../i18n";
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
  const { t } = useTranslation("monitor");
  const [propio, setPropio] = useState<RecordatorioTripulante | null>(null);
  const [equipo, setEquipo] = useState<RecordatoriosEquipo | null>(null);

  useRecargaPorClave(() => {
    if (!tripulanteId) return;
    let activo = true;
    api<RecordatorioTripulante>(`/recordatorios/${encodeURIComponent(tripulanteId)}`)
      .then((d) => { if (activo) setPropio(d); })
      .catch(() => { if (activo) setPropio(null); });
    api<RecordatoriosEquipo>("/recordatorios")
      .then((d) => { if (activo) setEquipo(d); })
      .catch(() => { if (activo) setEquipo(null); });
    return () => { activo = false; };
  }, estado, [tripulanteId]);

  if (!propio) return null;

  const titulo = propio.sin_capturas
    ? t("recordatorio.sinCapturas")
    : propio.vencido
      ? t("recordatorio.vencida", { min: propio.atrasado_min })
      : t("recordatorio.proxima", { min: propio.faltan_en_min });

  const resumenEquipo = equipo && equipo.vencidos > 0
    ? t("recordatorio.equipo", { n: equipo.vencidos })
    : "";

  if (propio.vencido || propio.sin_capturas) {
    return (
      <Alerta tono="aviso" titulo={titulo}>
        {t("recordatorio.intervalo", { min: propio.intervalo_min })}
        {propio.faltantes_news2.length > 0 && t("recordatorio.faltantes", { lista: propio.faltantes_news2.join(", ") })}
        {resumenEquipo}
      </Alerta>
    );
  }

  return (
    <section className="tarjeta recordatorio-ok" aria-label={t("recordatorio.aria")}>
      <p className="suave">
        <strong>{titulo}</strong> {t("recordatorio.intervaloOk", { min: propio.intervalo_min })}{resumenEquipo}
      </p>
    </section>
  );
}

