import { memo, useEffect, useRef, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import "./chat.css";

interface Respuesta { texto: string; fuente: string; generado_por_ia: boolean; aviso?: string; idioma?: string }
interface Saludo { texto: string; sugerencias: string[] }
interface Mensaje { de: "yo" | "asistente"; texto: string; aviso?: string }

const MAX_INTERESES = 160;

/** Conversación con Nova, tu compañía de apoyo (privada). Saludo y atajos: GET /asistente/saludo/{id}; chat: POST /asistente/chat/{id}
 *  con los últimos mensajes (el servidor no los guarda); perfil: GET/PUT /perfil-ia/{id}. */
function ChatAsistente({ tripulanteId }: { tripulanteId: string }) {
  const { t, i18n } = useTranslation("asistente");
  const idioma = (i18n?.language ?? "es").startsWith("en") ? "en" : "es";
  const [intereses, setIntereses] = useState("");
  const [rasgos, setRasgos] = useState("");
  const [guardado, setGuardado] = useState<{ ok: boolean; texto: string } | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [sugerencias, setSugerencias] = useState<string[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const fin = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setGuardado(null);
    setMensajes([]);
    setSugerencias([]);
    api<{ intereses: string; rasgos: string }>(`/perfil-ia/${tripulanteId}`)
      .then((p) => { setIntereses(p.intereses); setRasgos(p.rasgos ?? ""); })
      .catch(() => { setIntereses(""); setRasgos(""); });
    api<Saludo>(`/asistente/saludo/${tripulanteId}?idioma=${idioma}`)
      .then((s) => { setMensajes([{ de: "asistente", texto: s.texto }]); setSugerencias(s.sugerencias ?? []); })
      .catch(() => undefined);
  }, [tripulanteId, idioma]);

  useEffect(() => { fin.current?.scrollIntoView?.({ block: "end" }); }, [mensajes, enviando]);

  async function guardarPerfil() {
    try {
      const p = await api<{ intereses: string; rasgos: string }>(`/perfil-ia/${tripulanteId}`, { method: "PUT", body: JSON.stringify({ intereses, rasgos }) });
      setIntereses(p.intereses);
      setRasgos(p.rasgos ?? "");
      setGuardado({ ok: true, texto: t("chat.saved") });
    } catch (e) { setGuardado({ ok: false, texto: (e as Error).message }); }
  }

  async function enviar(mensaje?: string) {
    const pregunta = (mensaje ?? texto).trim();
    if (!pregunta || enviando) return;
    const historial = mensajes.slice(-6).map((m) => ({ rol: m.de, texto: m.texto.slice(0, 300) }));
    setTexto("");
    setSugerencias([]);
    setEnviando(true);
    setMensajes((m) => [...m, { de: "yo", texto: pregunta }]);
    try {
      const r = await api<Respuesta>(`/asistente/chat/${tripulanteId}`, { method: "POST", body: JSON.stringify({ texto: pregunta, historial }) });
      const aviso = r.generado_por_ia ? r.aviso : r.fuente === "reglas_locales" ? t("chat.escrito") : undefined;
      setMensajes((m) => [...m, { de: "asistente", texto: r.texto, aviso }]);
    } catch (e) {
      setMensajes((m) => [...m, { de: "asistente", texto: (e as Error).message }]);
    } finally { setEnviando(false); }
  }

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab">
        <div className="nova-cab">
          <span className="nova-avatar" aria-hidden="true">N</span>
          <div><h2>{t("chat.title")}</h2><p className="suave">{t("chat.hint")}</p></div>
        </div>
      </div>
      <div className="formulario">
        <div className="nova-log" role="log" aria-live="polite" aria-label={t("chat.title")}>
          {mensajes.map((m, i) => (
            <p key={i} className={`nova-burbuja ${m.de === "yo" ? "yo" : "nova"}`}>
              {m.texto}
              {m.aviso && <small className="nova-aviso">{m.aviso}</small>}
            </p>
          ))}
          {enviando && <p className="nova-burbuja nova" aria-label={t("chat.enviando")}><span className="nova-escribiendo"><i /><i /><i /></span></p>}
          <div ref={fin} />
        </div>
        {sugerencias.length > 0 && (
          <div className="nova-sugerencias" aria-label={t("chat.sugerencias")}>
            {sugerencias.map((s) => <button key={s} type="button" className="nova-chip" disabled={enviando} onClick={() => void enviar(s)}>{s}</button>)}
          </div>
        )}
        <div className="campo">
          <textarea id="chat-texto" className="redactor-texto" value={texto} maxLength={500} aria-label={t("chat.placeholder")}
                    onChange={(e) => setTexto(e.target.value)} placeholder={t("chat.placeholder")}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void enviar(); } }} />
          <button type="button" className="boton" onClick={() => void enviar()} disabled={enviando || !texto.trim()}>
            {enviando ? t("chat.enviando") : t("chat.enviar")}
          </button>
        </div>
        <details>
          <summary className="suave">{t("chat.perfil")}</summary>
          <div className="campo">
            <label className="campo-etiqueta" htmlFor="chat-intereses">{t("chat.intereses")}</label>
            <input id="chat-intereses" className="redactor-titulo" value={intereses} maxLength={MAX_INTERESES}
                   onChange={(e) => setIntereses(e.target.value)} onBlur={guardarPerfil} placeholder={t("chat.interesesEjemplo")} />
          </div>
          <div className="campo">
            <label className="campo-etiqueta" htmlFor="chat-rasgos">{t("chat.rasgos")}</label>
            <input id="chat-rasgos" className="redactor-titulo" value={rasgos} maxLength={MAX_INTERESES}
                   onChange={(e) => setRasgos(e.target.value)} onBlur={guardarPerfil} placeholder={t("chat.rasgosEjemplo")} />
          </div>
          {guardado && <Alerta tono={guardado.ok ? "ok" : "error"}>{guardado.texto}</Alerta>}
        </details>
      </div>
    </section>
  );
}

export default memo(ChatAsistente);
