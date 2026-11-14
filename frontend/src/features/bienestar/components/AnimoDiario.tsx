import { memo, useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import type { RespuestaAnimo, SerieAnimo } from "../types/bienestar";

const DIAS = 14;
const NIVELES = [1, 2, 3, 4, 5] as const;
const BOCAS: Record<number, string> = {
  1: "M8.5 17.5c1-2 2.2-3 3.5-3s2.5 1 3.5 3", 2: "M9 16.8c.8-1.2 1.8-1.8 3-1.8s2.2.6 3 1.8",
  3: "M9 16h6", 4: "M9 15c.8 1.2 1.8 1.8 3 1.8s2.2-.6 3-1.8", 5: "M8 14.5c.9 2.4 2.2 3.5 4 3.5s3.1-1.1 4-3.5z",
};

function Cara({ n }: { n: number }) {
  return (
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" />
      <circle cx="9" cy="10" r=".6" fill="currentColor" /><circle cx="15" cy="10" r=".6" fill="currentColor" />
      <path d={BOCAS[n]} />
    </svg>
  );
}

const W = 300, H = 96, PX = 14, PY = 12;

/** Linea de los ultimos dias (eje Y fijo 1-5) con la media punteada. */
function Linea({ serie }: { serie: SerieAnimo }) {
  const { t } = useTranslation("bienestar");
  const ahora = Date.now(), ini = ahora - DIAS * 86400000;
  const x = (ts: string) => PX + ((Math.max(ini, new Date(ts).getTime()) - ini) / (ahora - ini)) * (W - 2 * PX);
  const y = (v: number) => PY + ((5 - v) / 4) * (H - 2 * PY);
  const pts = serie.puntos.map((p) => [x(p.ts), y(p.valor)] as const);
  const d = pts.map(([px, py], i) => `${i ? "L" : "M"}${px.toFixed(1)} ${py.toFixed(1)}`).join(" ");
  const area = pts.length > 1 ? `${d} L${pts[pts.length - 1][0].toFixed(1)} ${H - PY} L${pts[0][0].toFixed(1)} ${H - PY} Z` : "";
  return (
    <svg className="animo-linea" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={serie.media !== null ? t("animo.chart.ariaMedia", { dias: DIAS, media: serie.media }) : t("animo.chart.aria", { dias: DIAS })}>
      {[1, 3, 5].map((v) => <line key={v} x1={PX} x2={W - PX} y1={y(v)} y2={y(v)} className="animo-guia" />)}
      {serie.media !== null && <line x1={PX} x2={W - PX} y1={y(serie.media)} y2={y(serie.media)} className="animo-media" />}
      {area && <path d={area} className="animo-area" />}
      {pts.length > 1 && <path d={d} className="animo-trazo" />}
      {pts.map(([px, py], i) => <circle key={i} cx={px} cy={py} r={i === pts.length - 1 ? 4.5 : 3} className={i === pts.length - 1 ? "animo-punto ultimo" : "animo-punto"} />)}
    </svg>
  );
}

function AnimoDiario({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("bienestar");
  const [serie, setSerie] = useState<SerieAnimo | null | "no">(null);
  const [resp, setResp] = useState<RespuestaAnimo | null>(null);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const cargar = useCallback(
    () => api<SerieAnimo>(`/animo/${tripulanteId}?dias=${DIAS}`).then(setSerie).catch(() => setSerie("no")),
    [tripulanteId],
  );
  useEffect(() => { setSerie(null); setResp(null); cargar(); }, [cargar]);

  async function elegir(valor: number) {
    if (enviando) return;
    setEnviando(true); setError("");
    try {
      setResp(await post<RespuestaAnimo>("/animo", { tripulante_id: tripulanteId, valor }));
      cargar();
    } catch (e) { setError((e as Error).message); } finally { setEnviando(false); }
  }

  const deHoy = serie && serie !== "no" ? serie.puntos.filter((p) => new Date(p.ts).toDateString() === new Date().toDateString()) : [];
  const hoy = deHoy.length ? deHoy[deHoy.length - 1].valor : undefined;
  const actual = resp?.valor ?? hoy;
  const n = serie && serie !== "no" ? serie.puntos.length : 0;

  return (
    <section className="tarjeta pieza animo">
      <div className="pieza-cab">
        <div>
          <h2>{t("animo.title")}</h2>
          <p className="suave">{t("animo.hint")}</p>
        </div>
      </div>

      <div className="animo-caras" role="group" aria-label={t("animo.group")}>
        {NIVELES.map((v) => (
          <button key={v} type="button" className={`cara cara-${v}${actual === v ? " elegida" : ""}`} aria-pressed={actual === v} disabled={enviando || serie === "no"} onClick={() => elegir(v)}>
            <Cara n={v} /><span>{t(`animo.nivel.${v}`)}</span>
          </button>
        ))}
      </div>

      {error && <Alerta tono="error">{error}</Alerta>}
      {serie === "no" && !error && <Alerta tono="info" titulo={t("animo.unavailable.title")}>{t("animo.unavailable.body")}</Alerta>}
      {resp && (
        <div className="animo-resp">
          {(resp.bajo || resp.aviso_linea_base) ? (
            <Alerta tono="aviso" titulo={resp.bajo ? t("animo.low.title") : t("animo.shift.title")}>
              {resp.bajo ? t("animo.low.body") : t("animo.shift.body")}
            </Alerta>
          ) : <Alerta tono="ok" titulo={t("animo.saved.title")}>{t("animo.saved.body")}</Alerta>}
          {resp.capsulas.map((c) => (
            <article key={c.id} className="capsula"><strong>{c.titulo}</strong><p>{c.contenido_markdown}</p></article>
          ))}
        </div>
      )}

      {serie && serie !== "no" && (
        <div className="animo-historial">
          <div className="animo-meta">
            <span className="campo-etiqueta">{t("animo.lastDays", { dias: DIAS })}</span>
            {serie.media !== null && <span className="animo-media-txt">{t("animo.mean")} <strong>{serie.media}</strong> / 5</span>}
          </div>
          {n === 0 ? <p className="vacio">{t("animo.empty")}</p> : <Linea serie={serie} />}
        </div>
      )}
    </section>
  );
}

export default memo(AnimoDiario);
