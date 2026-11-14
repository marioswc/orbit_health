import { FormEvent, memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { AvisoSaludMental, ProtocoloCrisis, RespuestaTamizaje } from "../types/bienestar";

const TOTAL_MAX = 6;

function Tamizaje({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("bienestar");
  const OPCIONES_CRISIS = [{ valor: "0", etiqueta: t("tamizaje.crisis.no") }, { valor: "1", etiqueta: t("tamizaje.crisis.yes") }];
  const [resp, setResp] = useState<(number | null)[]>([null, null]);
  const [riesgoAutolesion, setRiesgoAutolesion] = useState(false);
  const [calidadOxigeno, setCalidadOxigeno] = useState("");
  const [res, setRes] = useState<RespuestaTamizaje | null>(null);
  const [protocoloDirecto, setProtocoloDirecto] = useState<ProtocoloCrisis | null>(null);
  const [consentimiento, setConsentimiento] = useState(false);
  const [mensajeMedico, setMensajeMedico] = useState("");
  const [avisoActivo, setAvisoActivo] = useState<AvisoSaludMental | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRes(null);
    setProtocoloDirecto(null);
    setConsentimiento(false);
    setMensajeMedico("");
    setAvisoActivo(null);
    setError("");
  }, [tripulanteId]);

  const o2Numero = (): number | null => {
    if (!calidadOxigeno.trim()) return null;
    const v = Number(calidadOxigeno);
    return Number.isFinite(v) ? v : null;
  };

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (resp.some((r) => r === null)) return setError(t("tamizaje.answerBoth"));
    setError("");
    try {
      const r = await post<RespuestaTamizaje>("/tamizajes", {
        tripulante_id: tripulanteId,
        item1: resp[0],
        item2: resp[1],
        riesgo_autolesion: riesgoAutolesion,
        calidad_oxigeno: o2Numero(),
      });
      setRes(r);
      setProtocoloDirecto(null);
      setAvisoActivo(null);
      setConsentimiento(false);
    } catch (err) { setError((err as Error).message); }
  }

  async function abrirProtocoloEmergencia() {
    setError("");
    const o2 = o2Numero();
    const qs = new URLSearchParams({ tripulante_id: tripulanteId, nivel: "crisis" });
    if (o2 !== null) qs.set("calidad_oxigeno", String(o2));
    try {
      const p = await api<ProtocoloCrisis>(`/crisis/protocolo?${qs.toString()}`);
      setProtocoloDirecto(p);
    } catch (err) { setError((err as Error).message); }
  }

  async function compartirConMedico() {
    if (!consentimiento) return setError(t("tamizaje.needConsent"));
    setError("");
    const enCrisis = Boolean(protocoloDirecto || res?.nivel_protocolo === "crisis" || res?.riesgo_autolesion);
    try {
      const aviso = await post<AvisoSaludMental>("/crisis/aviso-medico", {
        tripulante_id: tripulanteId,
        consentimiento: true,
        tipo: enCrisis ? "crisis" : "tamizaje_positivo",
        tamizaje_id: res?.tamizaje_id ?? null,
        mensaje: mensajeMedico.trim() || null,
      });
      setAvisoActivo(aviso);
    } catch (err) { setError((err as Error).message); }
  }

  async function revocarAviso() {
    if (!avisoActivo) return;
    setError("");
    try {
      const rev = await post<AvisoSaludMental>(`/crisis/avisos/${avisoActivo.id}/revocar`, { tripulante_id: tripulanteId });
      setAvisoActivo(rev);
      setConsentimiento(false);
    } catch (err) { setError((err as Error).message); }
  }

  const protocoloVisible = protocoloDirecto ?? res?.protocolo ?? null;
  const o2Estado = protocoloVisible?.calidad_oxigeno ?? res?.calidad_oxigeno;
  const esCrisis = protocoloVisible?.nivel === "crisis" || res?.nivel_protocolo === "crisis" || Boolean(res?.riesgo_autolesion);
  const mostrarConsentimiento = Boolean(protocoloDirecto || res?.positivo);
  const capsulasVisibles = protocoloDirecto?.capsulas ?? res?.capsulas ?? [];

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab">
        <div>
          <h2>{t("tamizaje.title")}</h2>
          <p className="suave">{t("tamizaje.hint")}</p>
        </div>
        <button type="button" className="btn-secundario" onClick={abrirProtocoloEmergencia}>
          {t("tamizaje.crisisProtocol")}
        </button>
      </div>
      <form onSubmit={enviar} className="formulario">
        {[0, 1].map((i) => t(`tamizaje.q.${i}`)).map((p, i) => (
          <fieldset key={i} className="pregunta">
            <legend><span className="pregunta-num" aria-hidden="true">{i + 1}</span>{p}</legend>
            <Segmentado
              rejilla etiqueta={p} valor={resp[i] === null ? "" : String(resp[i])}
              alCambiar={(v) => { setResp(resp.map((r, j) => (j === i ? Number(v) : r))); setError(""); }}
              opciones={[0, 1, 2, 3].map((v) => ({ valor: String(v), etiqueta: t(`tamizaje.opt.${v}`) }))}
            />
          </fieldset>
        ))}
        <fieldset className="pregunta">
          <legend>
            <span className="pregunta-num" aria-hidden="true">3</span>
            {t("tamizaje.q3")}
          </legend>
          <Segmentado
            rejilla etiqueta={t("tamizaje.q3.aria")}
            valor={riesgoAutolesion ? "1" : "0"}
            alCambiar={(v) => { setRiesgoAutolesion(v === "1"); setError(""); }}
            opciones={OPCIONES_CRISIS}
          />
        </fieldset>
        <div className="campo">
          <label className="campo-etiqueta" htmlFor="tamizaje-o2">
            {t("tamizaje.o2.label")}
          </label>
          <input
            id="tamizaje-o2"
            type="number"
            step="0.1"
            min="10"
            max="35"
            value={calidadOxigeno}
            onChange={(e) => { setCalidadOxigeno(e.target.value); setError(""); }}
            placeholder={t("tamizaje.o2.placeholder")}
          />
        </div>
        <div className="fila-acciones">
          <button type="submit" className="btn-primario">{t("tamizaje.submit")}</button>
        </div>
        {error && <Alerta tono="error">{error}</Alerta>}
      </form>

      {(res || protocoloDirecto) && (
        <div className="resultado-tamizaje" role="status">
          {res && (
            <>
              <div className="medidor" aria-label={t("tamizaje.score.aria", { total: res.total, max: TOTAL_MAX })}>
                {Array.from({ length: TOTAL_MAX }, (_, i) => <span key={i} className={i < res.total ? "lleno" : ""} />)}
              </div>
              <Alerta
                tono={esCrisis ? "error" : res.positivo ? "aviso" : "ok"}
                titulo={t(esCrisis ? "tamizaje.score.crisis" : "tamizaje.score", { total: res.total, max: TOTAL_MAX })}
              >
                {esCrisis
                  ? t("tamizaje.res.crisis")
                  : res.positivo
                    ? t("tamizaje.res.positive")
                    : t("tamizaje.res.negative")}
              </Alerta>
            </>
          )}

          {o2Estado?.presente && o2Estado.nivel && (
            <Alerta
              tono={o2Estado.nivel === "rojo" ? "error" : o2Estado.nivel === "amarillo" ? "aviso" : "ok"}
              titulo={t("tamizaje.o2.title", { valor: String(o2Estado.valor_pct), nivel: o2Estado.nivel })}
            >
              {o2Estado.alerta
                ? t("tamizaje.o2.alert")
                : t("tamizaje.o2.ok")}
            </Alerta>
          )}

          {protocoloVisible && protocoloVisible.pasos.length > 0 && (
            <div className={`protocolo-crisis ${esCrisis ? "urgente" : ""}`}>
              <strong>{protocoloVisible.titulo}</strong>
              <ol className="protocolo-pasos">
                {protocoloVisible.pasos.map((paso) => <li key={paso}>{paso}</li>)}
              </ol>
              {protocoloVisible.contactos_abordo.length > 0 && (
                <p className="suave">
                  {t("tamizaje.contacts", { lista: protocoloVisible.contactos_abordo.map((c) => c.etiqueta).join(" · ") })}
                </p>
              )}
              <p className="suave">{protocoloVisible.aviso}</p>
            </div>
          )}

          {mostrarConsentimiento && (
            <div className="consentimiento-medico">
              <strong>{t("tamizaje.share.title")}</strong>
              <p className="suave">
                {t("tamizaje.share.hint")}
              </p>
              {avisoActivo && avisoActivo.estado !== "revocado" ? (
                <Alerta
                  tono="ok"
                  titulo={t("tamizaje.shared.title")}
                  accion={<button type="button" onClick={revocarAviso}>{t("tamizaje.revoke")}</button>}
                >
                  {t("tamizaje.shared.body", { estado: avisoActivo.estado })}
                </Alerta>
              ) : (
                <div className="consentimiento-controles">
                  {avisoActivo?.estado === "revocado" && (
                    <Alerta tono="info">{t("tamizaje.revoked")}</Alerta>
                  )}
                  <label className="consentimiento-check">
                    <input
                      type="checkbox"
                      checked={consentimiento}
                      onChange={(e) => { setConsentimiento(e.target.checked); setError(""); }}
                    />
                    <span>{t("tamizaje.consent")}</span>
                  </label>
                  <input
                    type="text"
                    value={mensajeMedico}
                    onChange={(e) => setMensajeMedico(e.target.value)}
                    placeholder={t("tamizaje.note.placeholder")}
                    maxLength={280}
                    aria-label={t("tamizaje.note.aria")}
                  />
                  <div className="fila-acciones">
                    <button type="button" className="btn-primario" onClick={compartirConMedico} disabled={!consentimiento}>
                      {t("tamizaje.notify")}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {capsulasVisibles.map((c) => (
            <article key={c.id} className="capsula">
              <strong>{c.titulo}</strong>
              <p>{c.contenido_markdown}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default memo(Tamizaje);
