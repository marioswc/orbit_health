import { useTranslation } from "../../../i18n";
import type { LecturaEstado } from "../types/estado";
import { FUENTE_EFECTOS, ZONAS, nivelZona, type Capa } from "../zonas";

import type { EntornoMision } from "../hooks/useEntornos";
import { nombreIndicador } from "../utils/nombreIndicador";
import ExplicacionIndicador from "./ExplicacionIndicador";
import { MESES_MAX, textoPerdida } from "../utils/perdidaOsea";

interface Props {
  id: string;
  lecturas: LecturaEstado[];
  capa: Capa;
  meses: number;
  alMeses: (m: number) => void;
  entorno?: EntornoMision | null;
}

export default function DetalleZona({ id, lecturas, capa, meses, alMeses, entorno = null }: Props) {
  const { t } = useTranslation("monitor");
  const zona = ZONAS.find((z) => z.id === id);
  if (!zona) return null;
  const nivel = nivelZona(zona.indicadores, lecturas);
  const dentro = lecturas.filter((l) => zona.indicadores.includes(l.indicador));
  const textoCapa = zona.anatomia[capa];
  const huesoDeCarga = capa === "hueso" && (zona.id === "brazos" || zona.id === "piernas");

  return (
    // key: al cambiar de zona se reinicia la animacion de entrada
    <section key={zona.id} className="detalle" aria-live="polite">
      <h2>{t(`zona.${zona.id}.etiqueta`)}</h2>
      <span className={`badge ${nivel}`}>{t(`common:status.${nivel}`)}</span>

      {capa !== "traje" && (
        <div className="capa-info" key={capa}>
          <h3>{t("detalle.capa", { capa: t(`capa.${capa}`) })}</h3>
          <p>{textoCapa ? t(`zona.${zona.id}.anat.${capa}`) : t("detalle.sinInfoCapa")}</p>
          {huesoDeCarga && (
            <div className="osea">
              {!entorno || entorno.microgravedad ? (
                <>
                  <label htmlFor="meses-mg">{t("detalle.tiempoMg")} <strong>{t("detalle.meses", { count: meses })}</strong></label>
                  <input id="meses-mg" type="range" min={0} max={MESES_MAX} step={1} value={meses} onChange={(e) => alMeses(Number(e.target.value))} />
                  <p className="osea-dato">
                    {t("detalle.perdida")} <strong>{textoPerdida(meses)}</strong>
                  </p>
                  <p className="fuente">{entorno?.estimacion_osea.nota ?? t("detalle.notaPerdida")}</p>
                </>
              ) : (
                <p className="fuente">
                  <strong>{entorno.nombre} ({entorno.gravedad_g !== null ? `${entorno.gravedad_g} g` : "gravedad variable"}):</strong>{" "}
                  {entorno.estimacion_osea.nota}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <h3>{t("detalle.indicadores")}</h3>
      {zona.indicadores.length === 0 && <p className="suave">{t("detalle.sinIndicadores")}</p>}
      {zona.indicadores.length > 0 && dentro.length === 0 && <p className="suave">{t("detalle.sinLecturas", { lista: zona.indicadores.join(", ") })}</p>}
      {dentro.map((l) => (
        <div key={l.indicador} className={`ind-fila ${l.nivel}`}>
          <div className="ind-dato">
            <span className="ind-nombre">{nombreIndicador(l.indicador, t)}<ExplicacionIndicador clave={l.indicador} /></span>
            <span className="ind-valor">{l.valor} {l.unidad}</span>
          </div>
          <span className={`badge ${l.nivel}`}>{t(`common:status.${l.nivel}`)}</span>
        </div>
      ))}

      <h3>{t("detalle.peligro", { peligro: t(`zona.${zona.id}.peligro`) })}</h3>
      <ul className="efectos">
        {zona.efectos.map((e, i) => <li key={e} style={{ ["--i" as string]: i }}>{t(`zona.${zona.id}.efecto.${i}`)}</li>)}
      </ul>
      <p className="fuente">{t("detalle.fuente", { fuente: FUENTE_EFECTOS })}</p>
    </section>
  );
}
