import { useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import type { Estado } from "../../monitor/types/estado";
import RelojBanda from "../components/RelojBanda";
import { useSimulacion } from "../hooks/useSimulacion";
import { VITALES_DEL_DIA, type Racha } from "../types/banda";

interface Props { tripulanteId: string; estado: Estado | null; refrescar: () => void }

/** Banda inteligente: el reloj con las lecturas reales, la mision simulada en vivo (las bandas "envian solas") y la racha de mediciones. */
export default function BandaPage({ tripulanteId, estado, refrescar }: Props) {
  const { t } = useTranslation("banda");
  const sim = useSimulacion(refrescar);
  const [racha, setRacha] = useState<Racha | null>(null);
  const activa = sim.estado?.activa ?? false;

  // La racha cambia cuando entran lecturas: se vuelve a pedir al empezar, al terminar y al cambiar de tripulante
  useEffect(() => { api<Racha>(`/racha/${tripulanteId}`).then(setRacha).catch(() => setRacha(null)); }, [tripulanteId, activa, sim.estado?.finalizada]);

  const lecturas = estado?.indicadores ?? [];
  const valor = (k: string) => lecturas.find((l) => l.indicador === k)?.valor;
  const signosHoy = racha ? Math.max(0, VITALES_DEL_DIA - racha.hoy_faltan.length) : 0;
  const e = sim.estado;
  const hecho = e ? e.eventos.filter((x) => x.ocurrido).length : 0;

  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t("page.kicker")} titulo={t("page.title")} descripcion={t("page.desc")}>
        {activa && <span className="chip-estado activo"><span className="latido" aria-hidden="true" />{t("sim.activa")}</span>}
      </EncabezadoPagina>

      <div className="banda">
        <section className="panel banda-reloj" aria-label={t("watch.title")}>
          <RelojBanda fc={valor("frecuencia_cardiaca")} spo2={valor("spo2")} news2={estado?.news2 && { puntos: estado.news2.puntos, nivel: estado.news2.nivel }} signosHoy={signosHoy} simulada={activa} />
          <p className="suave banda-nota">{t("watch.note")}</p>
        </section>

        <div className="banda-col">
          <section className="panel consola-panel" aria-label={t("sim.title")}>
            <h2>{t("sim.title")}</h2>
            <p className="suave">{t("sim.desc")}</p>
            {sim.error && <Alerta tono="error" titulo={t("sim.error")}>{sim.error}</Alerta>}
            {e?.aviso && <Alerta tono="aviso">{e.aviso}</Alerta>}
            {e?.error && <Alerta tono="error">{e.error}</Alerta>}
            <div className="sim-barra" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(e?.progreso_pct ?? 0)} aria-label={t("sim.progress")}>
              <span style={{ transform: `scaleX(${(e?.progreso_pct ?? 0) / 100})` }} />
            </div>
            <div className="sim-meta">
              <span>{t("sim.minute", { min: Math.floor(e?.minuto_mision ?? 0), total: e?.duracion_min ?? 34 })}</span>
              <span>{Math.round(e?.progreso_pct ?? 0)} %</span>
            </div>
            <div className="fila-acciones">
              {activa
                ? <button type="button" onClick={sim.detener}>{t("sim.stop")}</button>
                : <button type="button" className="btn-primario" onClick={sim.iniciar}>{e?.finalizada ? t("sim.again") : t("sim.start")}</button>}
              {e?.finalizada && !activa && <span className="suave">{t("sim.done")}</span>}
            </div>
          </section>

          <section className="panel consola-panel" aria-label={t("story.title")}>
            <h2>{t("story.title")}</h2>
            {!e || e.eventos.length === 0 ? <p className="suave">{t("story.empty")}</p> : (
              <ol className="historia">
                {e.eventos.map((x) => (
                  <li key={x.t_min} className={x.ocurrido ? "hecho" : ""}>
                    <span className="historia-min">{t("story.min", { min: x.t_min })}</span>
                    <span>{x.texto}</span>
                  </li>
                ))}
              </ol>
            )}
            {e && e.eventos.length > 0 && <p className="suave banda-nota">{t("story.progress", { hecho, total: e.eventos.length })}</p>}
          </section>

          <section className="panel consola-panel" aria-label={t("streak.title")}>
            <h2>{t("streak.title")}</h2>
            {!racha ? <p className="suave">{t("streak.none")}</p> : (
              <>
                <div className="racha-cifras">
                  <div><strong>{racha.racha_dias}</strong><span>{t("streak.days", { count: racha.racha_dias })}</span></div>
                  <div><strong>{racha.mejor_racha_dias}</strong><span>{t("streak.best")}</span></div>
                </div>
                <p className="suave">{racha.hoy_completo ? t("streak.todayDone") : t("streak.todayMissing", { lista: racha.hoy_faltan.join(", ") })}</p>
                <ul className="logros">{racha.logros.map((l) => <li key={l.id} className={l.logrado ? "logrado" : ""}>{l.nombre}</li>)}</ul>
              </>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
