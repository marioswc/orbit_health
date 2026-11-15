import { memo, useEffect, useRef, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";

interface Respuesta { texto: string; fuente: string; generado_por_ia: boolean; aviso?: string; idioma?: string }
interface Saludo { texto: string; sugerencias: string[] }
interface Mensaje { de: "yo" | "asistente"; texto: string; aviso?: string }

/** Conversación con Nova a pantalla completa, al estilo de un chat moderno: sin conversación, el saludo y el cuadro de texto van centrados;
 *  al empezar, los mensajes ocupan la pantalla y el cuadro queda abajo. Saludo y atajos: GET /asistente/saludo/{id};
 *  chat: POST /asistente/chat/{id} con los últimos mensajes (el servidor no los guarda). */
function ChatAsistente({ tripulanteId }: { tripulanteId: string }) {
  const { t, i18n } = useTranslation("asistente");
  const idioma = (i18n?.language ?? "es").startsWith("en") ? "en" : "es";
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [sugerencias, setSugerencias] = useState<string[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const fin = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMensajes([]);
    setSugerencias([]);
    api<Saludo>(`/asistente/saludo/${tripulanteId}?idioma=${idioma}`)
      .then((s) => { setMensajes([{ de: "asistente", texto: s.texto }]); setSugerencias(s.sugerencias ?? []); })
      .catch(() => undefined);
  }, [tripulanteId, idioma]);

  useEffect(() => { fin.current?.scrollIntoView?.({ block: "end" }); }, [mensajes, enviando]);

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

  const empezado = mensajes.some((m) => m.de === "yo");
  const saludo = !empezado ? mensajes[0] : undefined;
  // El saludo del servidor es largo: la primera frase va de titulo y el resto, mas pequeno
  const corte = saludo ? saludo.texto.search(/[.!?](\s|$)/) : -1;
  const titulo = saludo ? (corte > 0 ? saludo.texto.slice(0, corte + 1) : saludo.texto) : t("chat.title");
  const resto = saludo && corte > 0 ? saludo.texto.slice(corte + 1).trim() : "";

  const compositor = (
    <form className="gpt-compositor" onSubmit={(e) => { e.preventDefault(); void enviar(); }}>
      <textarea id="chat-texto" rows={1} value={texto} maxLength={500} aria-label={t("chat.placeholder")}
                onChange={(e) => setTexto(e.target.value)} placeholder={t("chat.placeholder")}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void enviar(); } }} />
      <div className="gpt-barra">
        <span className="gpt-contador" aria-hidden="true">{texto.length > 0 ? `${texto.length}/500` : ""}</span>
        <button type="submit" className="gpt-enviar" disabled={enviando || !texto.trim()} aria-label={enviando ? t("chat.enviando") : t("chat.enviar")} title={t("chat.enviar")}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
        </button>
      </div>
    </form>
  );

  return (
    <section className={`chat-gpt${empezado ? " activo" : " inicio"}`} aria-label={t("chat.title")}>
      {!empezado ? (
        <div className="gpt-inicio">
          <span className="nova-avatar grande" aria-hidden="true">N</span>
          <h2 className="gpt-titulo">{titulo}</h2>
          {resto && <p className="gpt-sub">{resto}</p>}
          {compositor}
          {sugerencias.length > 0 && (
            <div className="nova-sugerencias gpt-sug" aria-label={t("chat.sugerencias")}>
              {sugerencias.map((s) => <button key={s} type="button" className="nova-chip" disabled={enviando} onClick={() => void enviar(s)}>{s}</button>)}
            </div>
          )}
          <p className="gpt-nota">{t("chat.hint")}</p>
        </div>
      ) : (
        <>
          <div className="gpt-log" role="log" aria-live="polite" aria-label={t("chat.title")}>
            <div className="gpt-hilo">
              {mensajes.map((m, i) => (
                <div key={i} className={`gpt-fila ${m.de === "yo" ? "yo" : "nova"}`}>
                  {m.de === "asistente" && <span className="nova-avatar" aria-hidden="true">N</span>}
                  <p className={`nova-burbuja ${m.de === "yo" ? "yo" : "nova"}`}>
                    {m.texto}
                    {m.aviso && <small className="nova-aviso">{m.aviso}</small>}
                  </p>
                </div>
              ))}
              {enviando && (
                <div className="gpt-fila nova">
                  <span className="nova-avatar" aria-hidden="true">N</span>
                  <p className="nova-burbuja nova" aria-label={t("chat.enviando")}><span className="nova-escribiendo"><i /><i /><i /></span></p>
                </div>
              )}
              <div ref={fin} />
            </div>
          </div>
          <div className="gpt-pie">{compositor}<p className="gpt-nota">{t("chat.hint")}</p></div>
        </>
      )}
    </section>
  );
}

export default memo(ChatAsistente);
