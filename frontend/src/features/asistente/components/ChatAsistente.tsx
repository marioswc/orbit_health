import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";

interface Respuesta { texto: string; fuente: string; generado_por_ia: boolean; aviso?: string; nivel_general?: string }
interface Mensaje { de: "yo" | "asistente"; texto: string; aviso?: string }

const MAX_INTERESES = 160;

/** Conversación por texto con tu asistente (POST /api/asistente/chat/{id}) y tus intereses (GET/PUT /api/perfil-ia/{id}). Privado. */
function ChatAsistente({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  const [intereses, setIntereses] = useState("");
  const [guardado, setGuardado] = useState<{ ok: boolean; texto: string } | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    setGuardado(null);
    setMensajes([]);
    api<{ intereses: string }>(`/perfil-ia/${tripulanteId}`).then((p) => setIntereses(p.intereses)).catch(() => setIntereses(""));
  }, [tripulanteId]);

  async function guardarIntereses() {
    try {
      const p = await api<{ intereses: string }>(`/perfil-ia/${tripulanteId}`, { method: "PUT", body: JSON.stringify({ intereses }) });
      setIntereses(p.intereses);
      setGuardado({ ok: true, texto: t("chat.saved") });
    } catch (e) { setGuardado({ ok: false, texto: (e as Error).message }); }
  }

  async function enviar() {
    const pregunta = texto.trim();
    if (!pregunta || enviando) return;
    setTexto("");
    setEnviando(true);
    setMensajes((m) => [...m, { de: "yo", texto: pregunta }]);
    try {
      const r = await api<Respuesta>(`/asistente/chat/${tripulanteId}`, { method: "POST", body: JSON.stringify({ texto: pregunta }) });
      setMensajes((m) => [...m, { de: "asistente", texto: r.texto, aviso: r.generado_por_ia ? r.aviso : t("chat.escrito") }]);
    } catch (e) {
      setMensajes((m) => [...m, { de: "asistente", texto: (e as Error).message }]);
    } finally { setEnviando(false); }
  }

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab"><div><h2>{t("chat.title")}</h2><p className="suave">{t("chat.hint")}</p></div></div>
      <div className="formulario">
        <div className="campo">
          <label className="campo-etiqueta" htmlFor="chat-intereses">{t("chat.intereses")}</label>
          <input id="chat-intereses" className="redactor-titulo" value={intereses} maxLength={MAX_INTERESES}
                 onChange={(e) => setIntereses(e.target.value)} onBlur={guardarIntereses} placeholder={t("chat.interesesEjemplo")} />
        </div>
        {guardado && <Alerta tono={guardado.ok ? "ok" : "error"}>{guardado.texto}</Alerta>}
        <div role="log" aria-live="polite" aria-label={t("chat.title")}>
          {mensajes.map((m, i) => (
            <p key={i} className={m.de === "yo" ? "suave" : undefined}>
              <strong>{m.de === "yo" ? t("chat.yo") : t("chat.asistente")}:</strong> {m.texto}
              {m.aviso && <><br /><small className="suave">{m.aviso}</small></>}
            </p>
          ))}
        </div>
        <div className="campo">
          <textarea id="chat-texto" className="redactor-texto" value={texto} maxLength={500} aria-label={t("chat.placeholder")}
                    onChange={(e) => setTexto(e.target.value)} placeholder={t("chat.placeholder")}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void enviar(); } }} />
          <button type="button" className="boton" onClick={() => void enviar()} disabled={enviando || !texto.trim()}>
            {enviando ? t("chat.enviando") : t("chat.enviar")}
          </button>
        </div>
      </div>
    </section>
  );
}

export default memo(ChatAsistente);
