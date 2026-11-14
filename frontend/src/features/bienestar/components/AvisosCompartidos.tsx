import { memo, useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import type { AvisoSaludMental } from "../types/bienestar";

const hora = (ts: string, locale: string) => new Date(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(ts) ? `${ts.replace(" ", "T")}Z` : ts).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

/** Avisos que el propio tripulante compartio con el medico (GET /crisis/avisos/{id}); puede retirar su consentimiento. */
function AvisosCompartidos({ tripulanteId }: { tripulanteId: string }) {
  const { t, locale } = useTranslation("bienestar");
  const [avisos, setAvisos] = useState<AvisoSaludMental[] | null>(null);
  const [error, setError] = useState("");
  const cargar = useCallback(() => {
    api<AvisoSaludMental[]>(`/crisis/avisos/${tripulanteId}`).then((a) => { setAvisos(a); setError(""); }).catch((e) => { setAvisos([]); setError(e.message); });
  }, [tripulanteId]);
  useEffect(() => { setAvisos(null); cargar(); }, [cargar]);

  async function retirar(id: number) {
    try { await post(`/crisis/avisos/${id}/revocar`, { tripulante_id: tripulanteId }); cargar(); } catch (e) { setError((e as Error).message); }
  }

  if (avisos === null || (avisos.length === 0 && !error)) return null; // sin avisos no ocupa espacio
  return (
    <section className="tarjeta pieza" aria-label={t("avisos.aria")}>
      <div className="pieza-cab"><div><h2>{t("avisos.title")}</h2><p className="suave">{t("avisos.hint")}</p></div></div>
      {error && <Alerta tono="error">{error}</Alerta>}
      <ul className="avisos-lista">
        {avisos.map((a) => (
          <li key={a.id} className={`aviso-sm ${a.estado}`}>
            <div>
              <strong>{t(`avisos.tipo.${a.tipo}`)}</strong>
              <span className="suave">{hora(a.creado_ts, locale)}{a.mensaje_opcional ? ` · “${a.mensaje_opcional}”` : ""}</span>
            </div>
            <span className={`estado-aviso ${a.estado}`}>{t(`avisos.estado.${a.estado}`)}</span>
            {a.estado !== "revocado" && <button type="button" onClick={() => retirar(a.id)}>{t("avisos.withdraw")}</button>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default memo(AvisosCompartidos);
