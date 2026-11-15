import { useRef, useState } from "react";
import { getCurrentLanguage } from "../../../i18n";
import { getToken } from "../../../shared/api/client";
import { useExplicacionEstado } from "../hooks/useExplicacionEstado";
import type { Estado } from "../types/estado";

interface RespuestaVoz {
  transcripcion: string;
  texto: string;
  nivel_general: string;
  fuente?: string;
  generado_por_ia?: boolean;
  aviso?: string;
  audio_base64?: string;
  audio_media_type?: string;
}

interface Props {
  tripulanteId: string;
  estado: Estado | null;
}

/** Panel de asistente local (Santi style): resumen por IA local/reglas y consulta por voz offline. */
export default function AsistenteLocal({ tripulanteId, estado }: Props) {
  const { datos, cargando, recargar } = useExplicacionEstado(tripulanteId, estado);
  const [grabando, setGrabando] = useState(false);
  const [enviandoVoz, setEnviandoVoz] = useState(false);
  const [respuestaVoz, setRespuestaVoz] = useState<RespuestaVoz | null>(null);
  const [avisoVoz, setAvisoVoz] = useState<string | null>(null);
  const grabadoraRef = useRef<MediaRecorder | null>(null);
  const fragmentosRef = useRef<BlobPart[]>([]);

  const soportaMicrofono = typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";

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
        setAvisoVoz(typeof err.detail === "string" ? err.detail : `Voz no disponible (${r.status})`);
        return;
      }
      const res = (await r.json()) as RespuestaVoz;
      setRespuestaVoz(res);
      if (res.audio_base64) {
        const audio = new Audio(`data:${res.audio_media_type || "audio/wav"};base64,${res.audio_base64}`);
        audio.play().catch(() => { /* reproducción bloqueada por el navegador */ });
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
    if (!soportaMicrofono) return;
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

  if (!tripulanteId) return null;

  return (
    <section className="panel consola-panel" aria-label="Asistente local">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Asistente local</h2>
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
      </div>

      {cargando && !datos ? (
        <span className="esqueleto" style={{ height: 56 }} aria-busy="true" />
      ) : datos ? (
        <div style={{ display: "grid", gap: 10 }}>
          <p style={{ margin: 0, fontSize: "var(--text-body-sm)", lineHeight: 1.55, color: "var(--color-graphite)" }}>
            {datos.explicacion}
          </p>
          {datos.aviso && (
            <p className="suave" style={{ margin: 0, fontSize: "var(--text-caption)" }}>
              {datos.aviso}
            </p>
          )}
        </div>
      ) : (
        <p className="suave" style={{ margin: 0 }}>Sin resumen disponible.</p>
      )}

      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginTop: 14 }}>
        <button type="button" className="ghost" onClick={recargar} disabled={cargando}>
          {cargando ? "Actualizando…" : "Actualizar resumen"}
        </button>
        {soportaMicrofono && (
          <button
            type="button"
            className={grabando ? "btn-primario" : "ghost"}
            onClick={alternarGrabacion}
            disabled={enviandoVoz}
            aria-pressed={grabando}
          >
            {enviandoVoz ? "Procesando voz…" : grabando ? "Detener y enviar" : "Consultar por voz"}
          </button>
        )}
      </div>

      {avisoVoz && (
        <p className="suave" style={{ margin: "10px 0 0", fontSize: "var(--text-caption)" }}>
          {avisoVoz}
        </p>
      )}

      {respuestaVoz && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--color-stone)", display: "grid", gap: 6 }}>
          <p className="suave" style={{ margin: 0, fontSize: "var(--text-caption)" }}>
            Pregunta: “{respuestaVoz.transcripcion}”
          </p>
          <p style={{ margin: 0, fontSize: "var(--text-body-sm)", color: "var(--color-ink)" }}>
            {respuestaVoz.texto}
          </p>
        </div>
      )}
    </section>
  );
}
