import { memo } from "react";
import { useTranslation } from "../../../i18n";
import type { LecturaEstado } from "../types/estado";
import { nombreIndicador } from "../utils/indicadores";
import { compararConBase, formatoDelta } from "../utils/lineaBase";

interface Props {
  lectura: LecturaEstado;
  /** Destella al cambiar el valor (se usa tras la primera carga). */
  destello?: boolean;
  /** Si se pasa, permite abrir la grafica de historial al hacer clic. */
  activa?: boolean;
  alSeleccionar?: (indicador: string) => void;
  /** Si se pasa, permite abrir la explicacion pedagogica del indicador. */
  explicacionActiva?: boolean;
  alExplicar?: (indicador: string) => void;
}

/** Signo vital con su valor actual y la comparacion contra la linea base personal. */
function TarjetaSignoVital({ lectura: l, destello = false, activa = false, alSeleccionar, explicacionActiva = false, alExplicar }: Props) {
  const { t } = useTranslation("monitor");
  const c = compararConBase(l);
  const nombre = nombreIndicador(l.indicador, t);
  const nivelTxt = t(`common:status.${l.nivel}`);
  const fueraDeRango = l.nivel !== "verde";
  const normal = !fueraDeRango && !c.desvio;

  return (
    <article className={`signo ${l.nivel}${destello ? " destello" : ""}${activa ? " activa" : ""}`} aria-label={t("signo.aria", { nombre, valor: l.valor, unidad: l.unidad, nivel: nivelTxt })}>
      <header className="signo-cab">
        <span className="signo-nombre">{nombre}</span>
        <span className={`badge ${l.nivel}`}>{nivelTxt}</span>
      </header>
      <p className="signo-valor"><strong>{l.valor}</strong> <span>{l.unidad}</span></p>
      {c.disponible && c.media !== undefined && c.delta !== undefined ? (
        <p className="signo-base">{t("signo.base", { media: Number(c.media.toFixed(1)), unidad: l.unidad, delta: formatoDelta(c.delta) })}</p>
      ) : (
        <p className="signo-base suave">{t("signo.sinBase", { count: c.muestras })}</p>
      )}
      <p className="signo-estado">
        <span className="tendencia" aria-hidden="true">{c.tendencia}</span>
        {normal && <span className="etiqueta-estado">{t("signo.normal")}</span>}
        {fueraDeRango && <span className="etiqueta-estado alerta">{t("signo.fuera")}</span>}
        {c.desvio && <span className="etiqueta-estado desvio">{t("signo.desvio")}</span>}
        {alExplicar && (
          <button type="button" className="ghost signo-hist" onClick={() => alExplicar(l.indicador)} aria-pressed={explicacionActiva}>
            {explicacionActiva ? t("signo.ocultarInfo") : t("signo.queEs")}
          </button>
        )}
        {alSeleccionar && (
          <button type="button" className="ghost signo-hist" onClick={() => alSeleccionar(l.indicador)} aria-pressed={activa}>
            {activa ? t("signo.ocultarHist") : t("signo.historial")}
          </button>
        )}
      </p>
    </article>
  );
}

export default memo(TarjetaSignoVital);

