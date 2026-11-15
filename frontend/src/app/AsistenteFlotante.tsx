import { useEffect, useRef, useState } from "react";
import { getCurrentLanguage } from "../i18n";
import { getToken } from "../shared/api/client";
import { useExplicacionEstado } from "../features/monitor/hooks/useExplicacionEstado";
import type { Estado } from "../features/monitor/types/estado";

interface RespuestaVoz {
  transcripcion: string;
  texto: string;
  nivel_general: string;
  fuente?: string;
  generado_por_ia?: boolean;
  aviso?: string;
  audio_base64?: string;
  audio_media_type?: string;
  idioma?: "es" | "en";
}

interface Props {
  tripulanteId: string;
  estado: Estado | null;
}

/** Botón flotante tipo Siri: al abrirlo explica el estado con IA local/reglas y permite hablar por voz offline. */
export default function AsistenteFlotante({ tripulanteId, estado }: Props) {
  const [abierto, setAbierto] = useState(false);
  const { datos, cargando, recargar } = useExplicacionEstado(abierto ? tripulanteId : "", estado);
  const [grabando, setGrabando] = useState(false);
  const [enviandoVoz, setEnviandoVoz] = useState(false);
  const [hablando, setHablando] = useState(false);
  const [respuestaVoz, setRespuestaVoz] = useState<RespuestaVoz | null>(null);
  const [avisoVoz, setAvisoVoz] = useState<string | null>(null);
  const grabadoraRef = useRef<MediaRecorder | null>(null);
  const fragmentosRef = useRef<BlobPart[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const arrastreRef = useRef<{ px: number; py: number; bx: number; by: number; movido: boolean } | null>(null);

  function iniciarArrastre(e: React.PointerEvent<HTMLButtonElement>) {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    const rect = e.currentTarget.getBoundingClientRect();
    arrastreRef.current = { px: e.clientX, py: e.clientY, bx: rect.left, by: rect.top, movido: false };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }

  function moverArrastre(e: React.PointerEvent<HTMLButtonElement>) {
    const a = arrastreRef.current;
    if (!a) return;
    const dx = e.clientX - a.px;
    const dy = e.clientY - a.py;
    if (!a.movido && Math.hypot(dx, dy) > 6) a.movido = true;
    if (!a.movido) return;
    const maxX = Math.max(12, window.innerWidth - 68);
    const maxY = Math.max(12, window.innerHeight - 68);
    setPos({
      x: Math.min(maxX, Math.max(12, a.bx + dx)),
      y: Math.min(maxY, Math.max(12, a.by + dy)),
    });
  }

  function terminarArrastre(e: React.PointerEvent<HTMLButtonElement>) {
    const a = arrastreRef.current;
    arrastreRef.current = null;
    if (e.currentTarget.hasPointerCapture?.(e.pointerId)) {
      e.currentTarget.releasePointerCapture?.(e.pointerId);
    }
    if (!a?.movido) setAbierto((v) => !v);
  }

  const soportaMicrofono = typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
  const soportaVozNavegador = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  function detenerAudio() {
    audioRef.current?.pause();
    audioRef.current = null;
    if (soportaVozNavegador) window.speechSynthesis.cancel();
    setHablando(false);
  }

  function hablarTexto(texto: string, idioma: "es" | "en" = getCurrentLanguage()) {
    if (!soportaVozNavegador || !texto) return;
    detenerAudio();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = idioma === "en" ? "en-US" : "es-MX";
    u.rate = 1.02;
    u.onstart = () => setHablando(true);
    u.onend = () => setHablando(false);
    u.onerror = () => setHablando(false);
    window.speechSynthesis.speak(u);
  }

  async function enviarAudio(blob: Blob) {
    setEnviandoVoz(true);
    setAvisoVoz(null);
    try {
      const token = getToken();
      const headers: Record<string, string> = { "Content-Type": blob.type || "audio/webm" };
      if (token) headers.Authorization = `Bearer ${token}`;
      const r = await fetch(`/api/voz/chat/${encodeURIComponent(tripulanteId)}?idioma=${getCurrentLanguage()}`, {
        method: "POST",
        headers,
        body: blob,
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        setAvisoVoz(typeof err.detail === "string" ? err.detail : `Voz del servidor no disponible (${r.status}).`);
        return;
      }
      const res = (await r.json()) as RespuestaVoz;
      setRespuestaVoz(res);
      if (res.audio_base64) {
        detenerAudio();
        const audio = new Audio(`data:${res.audio_media_type || "audio/wav"};base64,${res.audio_base64}`);
        audioRef.current = audio;
        audio.onplay = () => setHablando(true);
        audio.onended = () => setHablando(false);
        audio.play().catch(() => setHablando(false));
      } else {
        hablarTexto(res.texto, res.idioma);
      }
    } catch {
      setAvisoVoz("No se pudo conectar con el servicio de voz local.");
    } finally {
      setEnviandoVoz(false);
    }
  }

  async function alternarGrabacion() {
    if (grabando) {
      grabadoraRef.current?.stop();
      setGrabando(false);
      return;
    }
    if (!soportaMicrofono) {
      setAvisoVoz("Este navegador no permite grabar audio desde el micrófono.");
      return;
    }
    detenerAudio();
    setAvisoVoz(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
      const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      fragmentosRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) fragmentosRef.current.push(e.data); };
      mr.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(fragmentosRef.current, { type: mr.mimeType || "audio/webm" });
        if (blob.size > 0) void enviarAudio(blob);
      };
      grabadoraRef.current = mr;
      mr.start();
      setGrabando(true);
    } catch {
      setAvisoVoz("No se pudo acceder al micrófono.");
    }
  }

  const panelStyle: React.CSSProperties | undefined = pos
    ? {
        left: Math.min(Math.max(12, pos.x - 310), Math.max(12, window.innerWidth - 382)),
        right: "auto",
        top: pos.y > 380 ? "auto" : pos.y + 68,
        bottom: pos.y > 380 ? Math.max(16, window.innerHeight - pos.y + 12) : "auto",
      }
    : undefined;

  return (
    <>
      {abierto && (
        <section className="cristal asistente-panel" style={panelStyle} role="dialog" aria-label="Asistente local ORBIT">
          <header className="asistente-cab">
            <div className="asistente-titulo">
              <span className={`asistente-punto${grabando || hablando ? " activo" : ""}`} aria-hidden="true" />
              <h2>Asistente local</h2>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {datos && (
                <span
                  className="badge"
                  style={{
                    background: datos.generado_por_ia ? "color-mix(in srgb, var(--hud) 14%, transparent)" : "var(--color-warm-taupe)",
                    color: datos.generado_por_ia ? "var(--hud)" : "var(--color-smoke)",
                    borderColor: datos.generado_por_ia ? "color-mix(in srgb, var(--hud) 35%, transparent)" : "var(--color-stone)",
                  }}
                >
                  {datos.generado_por_ia ? `IA local${datos.modelo ? ` · ${datos.modelo}` : ""}` : "Reglas locales"}
                </span>
              )}
              <button type="button" className="ghost asistente-cerrar" onClick={() => { detenerAudio(); setAbierto(false); }} aria-label="Cerrar asistente">
                ×
              </button>
            </div>
          </header>

          <div className="asistente-cuerpo">
            {cargando && !datos ? (
              <span className="esqueleto" style={{ height: 52 }} aria-busy="true" />
            ) : datos ? (
              <>
                <p className="asistente-texto">{datos.explicacion}</p>
                {datos.aviso && <p className="suave asistente-aviso">{datos.aviso}</p>}
              </>
            ) : (
              <p className="suave" style={{ margin: 0 }}>Sin resumen disponible.</p>
            )}

            {respuestaVoz && (
              <div className="asistente-chat">
                <p className="suave asistente-aviso">Tú: “{respuestaVoz.transcripcion}”</p>
                <p className="asistente-texto">{respuestaVoz.texto}</p>
              </div>
            )}

            {avisoVoz && <p className="suave asistente-aviso">{avisoVoz}</p>}
          </div>

          <footer className="asistente-pie">
            <button
              type="button"
              className={`asistente-orbe${grabando ? " grabando" : ""}`}
              onClick={alternarGrabacion}
              disabled={enviandoVoz}
              aria-pressed={grabando}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="9" y="2" width="6" height="12" rx="3" />
                <path d="M5 10a7 7 0 0 0 14 0M12 19v3M8 22h8" />
              </svg>
              <span>{enviandoVoz ? "Pensando…" : grabando ? "Detener y enviar" : "Hablar"}</span>
            </button>

            {soportaVozNavegador && datos && (
              <button
                type="button"
                className="ghost"
                onClick={() => (hablando ? detenerAudio() : hablarTexto(respuestaVoz?.texto ?? datos.explicacion))}
              >
                {hablando ? "Silenciar" : "Escuchar"}
              </button>
            )}

            <button type="button" className="ghost" onClick={recargar} disabled={cargando} aria-label="Actualizar resumen">
              ↻
            </button>
          </footer>
        </section>
      )}

      <button
        type="button"
        className={`btn-primario asistente-fab${abierto ? " abierto" : ""}${grabando || hablando ? " activo" : ""}`}
        style={pos ? { left: pos.x, top: pos.y, right: "auto", bottom: "auto" } : undefined}
        onPointerDown={iniciarArrastre}
        onPointerMove={moverArrastre}
        onPointerUp={terminarArrastre}
        onPointerCancel={() => { arrastreRef.current = null; }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setAbierto((v) => !v);
          }
        }}
        aria-expanded={abierto}
        aria-label="Asistente local"
        title="Asistente local (arrastra para mover)"
      >
        <svg className="asistente-ondas" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 3v18" />
          <path d="M8 7v10" />
          <path d="M16 7v10" />
          <path d="M4 11v2" />
          <path d="M20 11v2" />
        </svg>
      </button>
    </>
  );
}
