import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";

const MAX = 160;

interface Perfil { intereses: string; rasgos: string }

/** Lo que Nova sabe de ti (opcional): GET/PUT /perfil-ia/{id}. Se guarda al salir del campo y solo se usa con la IA de este equipo. */
function PerfilNova({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  const [intereses, setIntereses] = useState("");
  const [rasgos, setRasgos] = useState("");
  const [estado, setEstado] = useState<"" | "guardando" | "ok" | "error">("");
  const [error, setError] = useState("");

  useEffect(() => {
    setEstado(""); setError("");
    api<Perfil>(`/perfil-ia/${tripulanteId}`)
      .then((p) => { setIntereses(p.intereses); setRasgos(p.rasgos ?? ""); })
      .catch(() => { setIntereses(""); setRasgos(""); });
  }, [tripulanteId]);

  async function guardarPerfil() {
    setEstado("guardando");
    try {
      const p = await api<Perfil>(`/perfil-ia/${tripulanteId}`, { method: "PUT", body: JSON.stringify({ intereses, rasgos }) });
      setIntereses(p.intereses);
      setRasgos(p.rasgos ?? "");
      setEstado("ok"); setError("");
    } catch (e) { setEstado("error"); setError((e as Error).message); }
  }

  const campo = (id: string, etiqueta: string, ejemplo: string, valor: string, cambiar: (v: string) => void) => (
    <div className="perfil-campo">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="perfil-caja">
        <textarea id={id} rows={3} value={valor} maxLength={MAX} placeholder={ejemplo}
                  onChange={(e) => { cambiar(e.target.value); setEstado(""); }} onBlur={guardarPerfil} />
        <span className={`perfil-cuenta${valor.length >= MAX - 10 ? " limite" : ""}`} aria-hidden="true">{valor.length}/{MAX}</span>
      </div>
    </div>
  );

  return (
    <section className="tarjeta pieza perfil-nova">
      <div className="pieza-cab">
        <div className="nova-cab-mini">
          <span className="nova-avatar" aria-hidden="true">N</span>
          <div><h2>{t("chat.perfil")}</h2><p className="suave">{t("chat.perfilHint")}</p></div>
        </div>
      </div>
      <div className="perfil-campos">
        {campo("chat-intereses", t("chat.interesesCorto"), t("chat.interesesEjemplo"), intereses, setIntereses)}
        {campo("chat-rasgos", t("chat.rasgosCorto"), t("chat.rasgosEjemplo"), rasgos, setRasgos)}
      </div>
      <p className={`perfil-estado ${estado}`} role="status" aria-live="polite">
        {estado === "guardando" && t("chat.guardando")}
        {estado === "ok" && <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>{t("chat.saved")}</>}
        {estado === "error" && error}
      </p>
      <p className="perfil-privado">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
        {t("chat.privado")}
      </p>
    </section>
  );
}

export default memo(PerfilNova);
