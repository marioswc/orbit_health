import { memo } from "react";
import Alerta from "../../../shared/components/Alerta";
import { useTranslation } from "../../../i18n";
import type { Nivel } from "../../../shared/types/nivel";
import type { ReglaCombinada } from "../types/estado";

interface Props {
  nivel: Nivel | "sin_datos";
  proximaCapturaMin?: number;
  reglas?: ReglaCombinada[];
  acciones?: string[];
}

const TONO: Record<Nivel, "ok" | "aviso" | "error"> = { verde: "ok", amarillo: "aviso", rojo: "error" };

/** Reglas combinadas activas y pasos procedimentales sugeridos por el backend. */
function AccionesClinicas({ nivel, proximaCapturaMin, reglas = [], acciones = [] }: Props) {
  const { t } = useTranslation("monitor");
  if (reglas.length === 0 && acciones.length === 0 && proximaCapturaMin === undefined) return null;

  return (
    <section className="tarjeta acciones-clinicas" aria-label={t("acciones.aria")}>
      <div className="acciones-cab">
        <h2>{t("acciones.titulo")}</h2>
        {proximaCapturaMin !== undefined && (
          <span className="captura-rec">{t("acciones.repetir", { min: proximaCapturaMin })}</span>
        )}
      </div>

      {reglas.length > 0 && (
        <div className="reglas-activas" role="list" aria-label={t("acciones.reglasAria")}>
          {reglas.map((r) => (
            <div key={r.id} role="listitem">
              <Alerta tono={TONO[r.nivel]} titulo={r.nombre}>
                {t("acciones.cruce", { nivel: t(`common:status.${r.nivel}`) })}
              </Alerta>
            </div>
          ))}
        </div>
      )}

      {acciones.length > 0 && (
        <ul className="acciones-lista">
          {acciones.map((a) => <li key={a}>{a}</li>)}
        </ul>
      )}
    </section>
  );
}

export default memo(AccionesClinicas);
