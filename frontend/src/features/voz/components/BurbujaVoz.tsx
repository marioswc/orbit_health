import { useEffect, useRef, useState } from "react";
import { registrarEspanol, useTranslation } from "../../../i18n";
import esVoz from "../../../i18n/locales/ES/features/voz/voz.json";
import { getToken } from "../../../shared/api/client";
import "./voz.css";

registrarEspanol("voz", esVoz);

interface Props { tripulanteId: string }
interface Respuesta { texto: string; transcripcion: string; nivel_general?: string; fuente?: string; audio_base64?: string; audio_media_type?: string }
type Fase = "reposo" | "grabando" | "procesando";

const MAX_GRABACION_MS = 20_000;
const TIPOS = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
const ERRORES: Record<number, string> = { 503: "error.desactivada", 429: "error.ocupada", 413: "error.grande", 422: "error.noEntendi", 401: "error.sesion", 403: "error.sesion" };

/** Burbuja flotante de voz (push-to-talk): graba, envia el audio al backend local y muestra/reproduce la respuesta. Sin librerias. */
export default function BurbujaVoz({ tripulanteId }: Props) {
  const { t } = useTranslation("voz");
  const [fase, setFase] = useState<Fase>("reposo");
  const [abierta, setAbierta] = useState(false);
  const [respuesta, setRespuesta] = useState<Respuesta | null>(null);
  const [aviso, setAviso] = useState("");
  const [hablando, setHablando] = useState(false);
  const grabador = useRef<MediaRecorder | null>(null);
  const flujo = useRef<MediaStream | null>(null);
  const trozos = useRef<Blob[]>([]);
  const limite = useRef(0);
  const audio = useRef<HTMLAudioElement | null>(null);
  const desmontado = useRef(false);

  const soltarMicrofono = () => { flujo.current?.getTracks().forEach((p) => p.stop()); flujo.current = null; window.clearTimeout(limite.current); };
  useEffect(() => () => { desmontado.current = true; soltarMicrofono(); audio.current?.pause(); }, []);

  async function empezar() {
    setAviso(""); setRespuesta(null); setAbierta(true);
    audio.current?.pause(); setHablando(false);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") { setAviso(t("error.sinMicrofono")); return; }
    try {
      const f = await navigator.mediaDevices.getUserMedia({ audio: true });
      flujo.current = f;
      const tipo = TIPOS.find((x) => MediaRecorder.isTypeSupported(x));
      const g = new MediaRecorder(f, tipo ? { mimeType: tipo } : undefined);
      trozos.current = [];
      g.ondataavailable = (e) => { if (e.data.size) trozos.current.push(e.data); };
      g.onstop = () => { soltarMicrofono(); if (!desmontado.current) void enviar(new Blob(trozos.current, { type: g.mimeType || "audio/webm" })); };
      grabador.current = g;
      g.start();
      setFase("grabando");
      limite.current = window.setTimeout(() => detener(), MAX_GRABACION_MS);
    } catch {
      soltarMicrofono();
      setAviso(t("error.permiso"));
    }
  }

  function detener() {
    window.clearTimeout(limite.current);
    if (grabador.current && grabador.current.state !== "inactive") { setFase("procesando"); grabador.current.stop(); }
  }

  async function enviar(blob: Blob) {
    if (blob.size < 800) { setFase("reposo"); setAviso(t("error.vacio")); return; }
    setFase("procesando");
    try {
      const token = getToken();
      const r = await fetch(`/api/voz/chat/${encodeURIComponent(tripulanteId)}`, {
        method: "POST",
        headers: { "Content-Type": blob.type.split(";")[0] || "audio/webm", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: blob,
      });
      if (!r.ok) { setAviso(t(ERRORES[r.status] ?? "error.general")); return; }
      const d = (await r.json()) as Respuesta;
      setRespuesta(d);
      if (d.audio_base64) reproducir(d);
    } catch {
      setAviso(t("error.red"));
    } finally {
      setFase("reposo");
    }
  }

  function reproducir(d: Respuesta) {
    if (!d.audio_base64) return;
    audio.current?.pause();
    const a = new Audio(`data:${d.audio_media_type ?? "audio/wav"};base64,${d.audio_base64}`);
    audio.current = a;
    a.onplay = () => setHablando(true);
    a.onended = a.onpause = () => setHablando(false);
    void a.play().catch(() => setHablando(false));
  }

  function cerrar() { audio.current?.pause(); setHablando(false); setAbierta(false); setRespuesta(null); setAviso(""); }

  const grabando = fase === "grabando";
  const procesando = fase === "procesando";
  const etiquetaBoton = grabando ? t("boton.detener") : procesando ? t("boton.procesando") : t("boton.hablar");
  const esIA = respuesta?.fuente !== undefined && respuesta.fuente !== "reglas_locales";

  return (
    <div className="voz">
      {abierta && (
        <div className="voz-panel" role="dialog" aria-label={t("titulo")} aria-live="polite">
          <div className="voz-cab">
            <strong>{t("titulo")}</strong>
            <button type="button" className="ghost icono" onClick={cerrar} aria-label={t("cerrar")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </div>
          {grabando && <p className="voz-estado"><span className="voz-onda" aria-hidden="true"><i /><i /><i /><i /></span>{t("estado.escuchando")}</p>}
          {procesando && <p className="voz-estado">{t("estado.procesando")}</p>}
          {aviso && <p className="voz-aviso" role="alert">{aviso}</p>}
          {respuesta && (
            <>
              {respuesta.transcripcion && <p className="voz-tu"><span>{t("tu")}</span>{respuesta.transcripcion}</p>}
              <p className="voz-resp">{respuesta.texto}</p>
              <p className="voz-ia">{esIA ? t("etiqueta.ia") : t("etiqueta.reglas")}</p>
              {respuesta.audio_base64 && (
                <button type="button" className="ghost" onClick={() => reproducir(respuesta)} disabled={hablando}>{hablando ? t("escuchando") : t("repetir")}</button>
              )}
            </>
          )}
          {!grabando && !procesando && !respuesta && !aviso && <p className="voz-estado">{t("ayuda")}</p>}
        </div>
      )}
      <button type="button" className={`voz-bola${grabando ? " grabando" : ""}${procesando ? " procesando" : ""}`}
        onClick={grabando ? detener : empezar} disabled={procesando} aria-label={etiquetaBoton} aria-pressed={grabando} title={etiquetaBoton}>
        {grabando ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="3" /></svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg>
        )}
      </button>
    </div>
  );
}
