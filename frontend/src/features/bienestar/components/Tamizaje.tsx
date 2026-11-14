import { FormEvent, memo, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { AvisoSaludMental, ProtocoloCrisis, RespuestaTamizaje } from "../types/bienestar";

const OPCIONES = ["Nunca", "Varios días", "Más de la mitad de los días", "Casi todos los días"];
const PREGUNTAS = [
  "Poco interés o placer en hacer las cosas",
  "Sentirse desanimado, deprimido o sin esperanza",
];
const OPCIONES_CRISIS = [
  { valor: "0", etiqueta: "No" },
  { valor: "1", etiqueta: "Sí, necesito protocolo de apoyo inmediato" },
];
const TOTAL_MAX = 6;

function Tamizaje({ tripulanteId }: { tripulanteId: string }) {
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
    if (resp.some((r) => r === null)) return setError("Responde las dos preguntas");
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
    if (!consentimiento) return setError("Marca la casilla de consentimiento para avisar al médico de a bordo");
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
          <h2>Tamizaje de ánimo (PHQ-2) y protocolo de crisis</h2>
          <p className="suave">Últimas dos semanas. Resultado privado: no se transmite. Es un tamizaje, no un diagnóstico.</p>
        </div>
        <button type="button" className="btn-secundario" onClick={abrirProtocoloEmergencia}>
          Protocolo de crisis
        </button>
      </div>
      <form onSubmit={enviar} className="formulario">
        {PREGUNTAS.map((p, i) => (
          <fieldset key={p} className="pregunta">
            <legend><span className="pregunta-num" aria-hidden="true">{i + 1}</span>{p}</legend>
            <Segmentado
              rejilla etiqueta={p} valor={resp[i] === null ? "" : String(resp[i])}
              alCambiar={(v) => { setResp(resp.map((r, j) => (j === i ? Number(v) : r))); setError(""); }}
              opciones={OPCIONES.map((o, v) => ({ valor: String(v), etiqueta: o }))}
            />
          </fieldset>
        ))}
        <fieldset className="pregunta">
          <legend>
            <span className="pregunta-num" aria-hidden="true">3</span>
            ¿Atraviesas una crisis psicológica aguda o has tenido pensamientos de hacerte daño?
          </legend>
          <Segmentado
            etiqueta="Pregunta de seguridad ante crisis o autolesión"
            valor={riesgoAutolesion ? "1" : "0"}
            alCambiar={(v) => { setRiesgoAutolesion(v === "1"); setError(""); }}
            opciones={OPCIONES_CRISIS}
          />
        </fieldset>
        <div className="campo">
          <label className="campo-etiqueta" htmlFor="tamizaje-o2">
            Calidad de oxígeno en cabina (% O₂, opcional; si se omite usa la última lectura de la nave)
          </label>
          <input
            id="tamizaje-o2"
            type="number"
            step="0.1"
            min="10"
            max="35"
            value={calidadOxigeno}
            onChange={(e) => { setCalidadOxigeno(e.target.value); setError(""); }}
            placeholder="Ej. 21.0 (normal: 19.5 % – 23.0 %)"
          />
        </div>
        <div className="fila-acciones">
          <button type="submit" className="btn-primario">Ver resultado</button>
        </div>
        {error && <Alerta tono="error">{error}</Alerta>}
      </form>

      {(res || protocoloDirecto) && (
        <div className="resultado-tamizaje" role="status">
          {res && (
            <>
              <div className="medidor" aria-label={`Puntaje ${res.total} de ${TOTAL_MAX}`}>
                {Array.from({ length: TOTAL_MAX }, (_, i) => <span key={i} className={i < res.total ? "lleno" : ""} />)}
              </div>
              <Alerta
                tono={esCrisis ? "error" : res.positivo ? "aviso" : "ok"}
                titulo={esCrisis ? `Protocolo de crisis activo · Puntaje ${res.total}/${TOTAL_MAX}` : `Puntaje ${res.total}/${TOTAL_MAX}`}
              >
                {esCrisis
                  ? "Riesgo agudo detectado: sigue los pasos inmediatos de acompañamiento y verificación ambiental a bordo."
                  : res.positivo
                    ? "Positivo en tamizaje. No es un diagnóstico: conviene hablarlo con el médico a bordo."
                    : "Negativo en tamizaje."}
              </Alerta>
            </>
          )}

          {o2Estado?.presente && o2Estado.nivel && (
            <Alerta
              tono={o2Estado.nivel === "rojo" ? "error" : o2Estado.nivel === "amarillo" ? "aviso" : "ok"}
              titulo={`Calidad de oxígeno en cabina: ${o2Estado.valor_pct} % (${o2Estado.nivel})`}
            >
              {o2Estado.alerta
                ? "La hipoxia o alteración del O₂ en cabina puede provocar o agravar angustia, confusión y crisis psicológica aguda."
                : "Oxígeno de cabina dentro del rango nominal."}
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
                  Contactos a bordo: {protocoloVisible.contactos_abordo.map((c) => c.etiqueta).join(" · ")}
                </p>
              )}
              <p className="suave">{protocoloVisible.aviso}</p>
            </div>
          )}

          {mostrarConsentimiento && (
            <div className="consentimiento-medico">
              <strong>Compartir con el médico de a bordo (opcional y con tu consentimiento)</strong>
              <p className="suave">
                Solo el médico o comandante a bordo verá este aviso. No comparte tu diario personal ni entra en la cola hacia Tierra.
              </p>
              {avisoActivo && avisoActivo.estado !== "revocado" ? (
                <Alerta
                  tono="ok"
                  titulo="Aviso compartido con el médico de a bordo"
                  accion={<button type="button" onClick={revocarAviso}>Revocar consentimiento</button>}
                >
                  Estado: {avisoActivo.estado}. Puedes retirar tu consentimiento en cualquier momento.
                </Alerta>
              ) : (
                <div className="consentimiento-controles">
                  {avisoActivo?.estado === "revocado" && (
                    <Alerta tono="info">Consentimiento revocado. El aviso ya no es visible para el médico de a bordo.</Alerta>
                  )}
                  <label className="consentimiento-check">
                    <input
                      type="checkbox"
                      checked={consentimiento}
                      onChange={(e) => { setConsentimiento(e.target.checked); setError(""); }}
                    />
                    <span>Autorizo avisar al médico de a bordo para recibir acompañamiento en cabina</span>
                  </label>
                  <input
                    type="text"
                    value={mensajeMedico}
                    onChange={(e) => setMensajeMedico(e.target.value)}
                    placeholder="Nota breve opcional para el médico (máx. 280 caracteres)"
                    maxLength={280}
                    aria-label="Nota opcional para el médico de a bordo"
                  />
                  <div className="fila-acciones">
                    <button type="button" className="btn-primario" onClick={compartirConMedico} disabled={!consentimiento}>
                      Avisar al médico con mi consentimiento
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
