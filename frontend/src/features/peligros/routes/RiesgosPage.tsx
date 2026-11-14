import { useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import { nombreIndicador } from "../../monitor/utils/nombreIndicador";
import type { MarcoPeligros } from "../types/peligros";

/** Marco de peligros y riesgos del HRP de la NASA y lo que ORBIT Health cubre de verdad (sin prometer de mas). El texto de cada peligro lo entrega el backend. */
export default function RiesgosPage() {
  const { t } = useTranslation("riesgos");
  const { t: tm } = useTranslation("monitor");
  const [marco, setMarco] = useState<MarcoPeligros | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api<MarcoPeligros>("/peligros").then(setMarco).catch((e) => setError(e.message)); }, []);

  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t("page.kicker")} titulo={t("page.title")} descripcion={t("page.desc")}>
        {marco && (
          <span className="chip-estado" aria-label={t("chip.aria")}>
            {t("chip.summary", { c: marco.resumen_cobertura.cubierto, p: marco.resumen_cobertura.parcial, n: marco.resumen_cobertura.no_cubierto, t: marco.resumen_cobertura.total })}
          </span>
        )}
      </EncabezadoPagina>
      {error && <Alerta tono="error" titulo={t("loadError")}>{error}</Alerta>}
      {!marco && !error && <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      {marco && (
        <>
          <section className="peligros-rejilla" aria-label={t("hazards.aria")}>
            {Object.entries(marco.peligros).map(([id, p]) => (
              <article key={id} className="tarjeta pieza peligro">
                <h2>{p.nombre}</h2>
                <p className="suave">{p.resumen}</p>
                <p className="peligro-orbit"><strong>{t("hazards.how")}</strong>{p.como_responde_orbit}</p>
                <a className="enlace" href={p.url} target="_blank" rel="noopener noreferrer">{t("hazards.nasa", { nombre: p.nombre_oficial })}</a>
              </article>
            ))}
          </section>
          <section className="tarjeta pieza" aria-label={t("risks.aria")}>
            <h2>{t("risks.title")}</h2>
            <p className="suave">{t("risks.note")}</p>
            <ul className="riesgos">
              {marco.riesgos.map((r) => (
                <li key={r.nombre_oficial}>
                  <span className={`cobertura ${r.cobertura}`}>{t(`cover.${r.cobertura}`)}</span>
                  <a className="enlace" href={r.url} target="_blank" rel="noopener noreferrer">{r.nombre_oficial.replace(/^Risk of /, "")}</a>
                  {r.indicadores.length > 0 && <span className="riesgo-ind">{r.indicadores.map((k) => nombreIndicador(k, tm)).join(" · ")}</span>}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
