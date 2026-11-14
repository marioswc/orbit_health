import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { AvisoSaludMental } from "../../bienestar/types/bienestar";

/** Vista del medico o comandante: avisos de salud mental con consentimiento vigente (GET /crisis/avisos) y marcarlos atendidos. */
export default function AvisosMedico() {
  const { t, locale } = useTranslation("sistema");
  const hora = (ts: string) => new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(ts) ? `${ts.replace(" ", "T")}Z` : ts).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const [pendientes, setPendientes] = useState("si");
  const [avisos, setAvisos] = useState<AvisoSaludMental[] | null>(null);
  const [error, setError] = useState("");
  const cargar = useCallback(() => {
    api<AvisoSaludMental[]>(`/crisis/avisos?solo_pendientes=${pendientes === "si"}`).then((a) => { setAvisos(a); setError(""); }).catch((e) => { setAvisos([]); setError(e.message); });
  }, [pendientes]);
  useEffect(() => { cargar(); }, [cargar]);

  async function atender(id: number) {
    try { await post(`/crisis/avisos/${id}/atender`, {}); cargar(); } catch (e) { setError((e as Error).message); }
  }

  return (
    <section className="tarjeta pieza" aria-label={t("crisis.title")}>
      <div className="pieza-cab">
        <div><h2>{t("crisis.title")}</h2><p className="suave">{t("crisis.desc")}</p></div>
        <Segmentado etiqueta={t("crisis.filter")} valor={pendientes} alCambiar={setPendientes} opciones={[{ valor: "si", etiqueta: t("crisis.pending") }, { valor: "no", etiqueta: t("crisis.all") }]} />
      </div>
      {error && <Alerta tono="error" titulo={t("crisis.readError")}>{error}</Alerta>}
      {avisos === null && <span className="esqueleto" style={{ height: 80 }} aria-busy="true" />}
      {avisos && avisos.length === 0 && !error && <p className="vacio">{pendientes === "si" ? t("crisis.emptyPending") : t("crisis.empty")}</p>}
      {avisos && avisos.length > 0 && (
        <ul className="avisos-lista">
          {avisos.map((a) => (
            <li key={a.id} className={`aviso-sm ${a.estado} ${a.nivel_protocolo}`}>
              <div>
                <strong>{a.tripulante_id} · {t(`crisis.type.${a.tipo}`)}</strong>
                <span className="suave">{hora(a.creado_ts)} · {t("crisis.protocol", { nivel: a.nivel_protocolo })}{a.mensaje_opcional ? ` · “${a.mensaje_opcional}”` : ""}</span>
              </div>
              <span className={`estado-aviso ${a.estado}`}>{t(`crisis.state.${a.estado}`)}</span>
              {a.estado === "pendiente" && <button type="button" className="btn-primario" onClick={() => atender(a.id)}>{t("crisis.attend")}</button>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
