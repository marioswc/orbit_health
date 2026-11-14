import { memo } from "react";
import { useTranslation } from "../../../i18n";
import type { AlertaColectiva } from "../types/cabina";
import type { Ambiente } from "../utils/ambiente";

interface Props {
  ambiente: Ambiente;
  alerta: AlertaColectiva | null;
}

/** Aire (CO2) y radiacion acumulada de la cabina, con la alerta colectiva cuando aplica. */
function MonitorCabina({ ambiente, alerta }: Props) {
  const { t } = useTranslation("cabina");
  const { co2, co2Nivel, dosis } = ambiente;
  const pct = dosis ? Math.min(100, Math.max(0, dosis.valor)) : 0;

  return (
    <div className="panel cabina" role="region" aria-label={t("aria")}>
      <h2>{t("titulo")}</h2>

      <div className="cabina-dato">
        <span className="cabina-rotulo">{t("co2")}</span>
        {co2 !== null ? (
          <>
            <p className="cabina-valor"><strong>{co2}</strong> <span>mmHg</span></p>
            {co2Nivel ? (
              <p className="cabina-estado"><span className={`badge ${co2Nivel}`}>{t(`common:status.${co2Nivel}`)}</span><span className="suave">{t(`co2.desc.${co2Nivel}`)}</span></p>
            ) : (
              <p className="suave">{t("co2.sinNivel")}</p>
            )}
          </>
        ) : (
          <p className="suave">{t("co2.sinLectura")}</p>
        )}
      </div>

      <div className="cabina-dato">
        <span className="cabina-rotulo">{t("dosis")}</span>
        {dosis ? (
          <>
            <p className="cabina-valor"><strong>{dosis.valor}</strong> <span>{t("dosis.limite")}</span></p>
            <div className="medidor" role="progressbar" aria-label={t("dosis.aria")} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
              <span className={`medidor-relleno ${dosis.nivel}`} style={{ transform: `scaleX(${pct / 100})` }} />
            </div>
            <p className="cabina-estado"><span className={`badge ${dosis.nivel}`}>{t(`common:status.${dosis.nivel}`)}</span></p>
          </>
        ) : (
          <p className="suave">{t("dosis.sinLectura")}</p>
        )}
      </div>

      {alerta && (
        <div className="cabina-alerta" role="alert">
          <span className={`badge ${alerta.nivel}`}>{t(`common:status.${alerta.nivel}`)}</span>
          <strong>{alerta.nombre}</strong>
          <p>{t("alerta.afectados", { count: alerta.afectados, co2: alerta.co2_mmhg })}</p>
        </div>
      )}

      <p className="fuente">{t("umbrales")}</p>
    </div>
  );
}

export default memo(MonitorCabina);

