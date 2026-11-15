import { useEffect, useRef, useState } from "react";
import { registrarEspanol, useTranslation } from "../../../i18n";
import esVoz from "../../../i18n/locales/ES/features/voz/voz.json";
import { getToken } from "../../../shared/api/client";
import "./voz.css";

registrarEspanol("voz", esVoz);

interface Props { tripulanteId: string }
interface Respuesta { texto: string; transcripcion: string; nivel_general?: string; fuente?: string; idioma?: "es" | "en"; audio_base64?: string; audio_media_type?: string }
type Fase = "reposo" | "grabando" | "procesando";

const MAX_GRABACION_MS = 20_000;
const MAX_PROCESAMIENTO_MS = 60_000;
const TIPOS = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
const ERRORES: Record<number, string> = { 503: "error.desactivada", 429: "error.ocupada", 413: "error.grande", 422: "error.noEntendi", 401: "error.sesion", 403: "error.sesion" };

const puedeHablar = () => typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";

/** Prefiere una voz en espanol instalada en el equipo (localService): funciona sin red. */
function vozLocal(idioma: "es" | "en"): SpeechSynthesisVoice | undefined {
  const prefijo = idioma === "en" ? "en" : "es";
  const voces = window.speechSynthesis.getVoices().filter((v) => v.lang.toLowerCase().startsWith(prefijo));
  const exacta = idioma === "en" ? "en-US" : "es-MX";
  return voces.find((v) => v.localService && v.lang.toLowerCase() === exacta.toLowerCase())
    ?? voces.find((v) => v.localService)
    ?? voces[0];
}

/** Burbuja flotante de voz (push-to-talk): graba, envia el audio al backend local y muestra/reproduce la respuesta. Sin librerias. */
export default function BurbujaVoz({ tripulanteId }: Props) {
  const { t, i18n } = useTranslation("voz");
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
  const contenedor = useRef<HTMLDivElement | null>(null);
  const detenerNivel = useRef<(() => void) | null>(null);

  const soltarMicrofono = () => {
    detenerNivel.current?.();
    detenerNivel.current = null;
    contenedor.current?.style.setProperty("--voz-nivel", "0");
    flujo.current?.getTracks().forEach((p) => p.stop());
    flujo.current = null;
    window.clearTimeout(limite.current);
  };
  // StrictMode (dev) monta -> desmonta -> vuelve a montar: hay que reiniciar la bandera al montar,
  // si no queda en true para siempre y onstop nunca envia el audio (se queda en "procesando").
  useEffect(() => {
    desmontado.current = false;
    return () => { desmontado.current = true; soltarMicrofono(); audio.current?.pause(); if (puedeHablar()) window.speechSynthesis.cancel(); };
  }, []);

  function observarNivel(f: MediaStream) {
    try {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!Ctx) return;
      const ctx = new Ctx();
      const fuente = ctx.createMediaStreamSource(f);
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 64;
      fuente.connect(analizador);
      const datos = new Uint8Array(analizador.frequencyBinCount);
      let raf = 0;
      const medir = () => {
        analizador.getByteFrequencyData(datos);
        let suma = 0;
        for (let i = 0; i < datos.length; i++) suma += datos[i];
        const prom = Math.min(1, suma / (datos.length * 140));
        contenedor.current?.style.setProperty("--voz-nivel", prom.toFixed(2));
        raf = window.requestAnimationFrame(medir);
      };
      raf = window.requestAnimationFrame(medir);
      detenerNivel.current = () => { window.cancelAnimationFrame(raf); void ctx.close().catch(() => {}); };
    } catch {
      /* En entornos sin Web Audio (p. ej. jsdom) la animacion CSS funciona sola */
    }
  }

  async function empezar() {
    setAviso(""); setRespuesta(null); setAbierta(true);
    callar();
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") { setAviso(t("error.sinMicrofono")); return; }
    try {
      const f = await navigator.mediaDevices.getUserMedia({ audio: true });
      flujo.current = f;
      const tipo = TIPOS.find((x) => MediaRecorder.isTypeSupported(x));
      const g = new MediaRecorder(f, tipo ? { mimeType: tipo } : undefined);
      trozos.current = [];
      g.ondataavailable = (e) => { if (e.data.size) trozos.current.push(e.data); };
      g.onstop = () => {
        soltarMicrofono();
        if (desmontado.current) return;
        void enviar(new Blob(trozos.current, { type: g.mimeType || "audio/webm" }));
      };
      grabador.current = g;
      g.start();
      observarNivel(f);
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
    const controlador = new AbortController();
    const limiteProcesamiento = window.setTimeout(() => controlador.abort(), MAX_PROCESAMIENTO_MS);
    try {
      const token = getToken();
      const r = await fetch(`/api/voz/chat/${encodeURIComponent(tripulanteId)}?idioma=${i18n.language}`, {
        method: "POST",
        headers: { "Content-Type": blob.type.split(";")[0] || "audio/webm", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: blob,
        signal: controlador.signal,
      });
      if (!r.ok) { setAviso(t(ERRORES[r.status] ?? "error.general")); return; }
      const d = (await r.json()) as Respuesta;
      setRespuesta(d);
      reproducir(d);
    } catch (error) {
      setAviso(error instanceof DOMException && error.name === "AbortError" ? t("error.tiempo") : t("error.red"));
    } finally {
      window.clearTimeout(limiteProcesamiento);
      setFase("reposo");
    }
  }

  function callar() {
    audio.current?.pause();
    if (puedeHablar()) window.speechSynthesis.cancel();
    setHablando(false);
  }

  /** Audio de Piper si el backend lo genero; si no, voz del sistema operativo (local, sin internet). */
  function reproducir(d: Respuesta) {
    callar();
    if (d.audio_base64) {
      const a = new Audio(`data:${d.audio_media_type ?? "audio/wav"};base64,${d.audio_base64}`);
      audio.current = a;
      a.onplay = () => setHablando(true);
      a.onended = a.onpause = () => setHablando(false);
      void a.play().catch(() => setHablando(false));
      return;
    }
    if (!puedeHablar() || !d.texto) return;
    const idioma = d.idioma ?? i18n.language;
    const u = new SpeechSynthesisUtterance(d.texto);
    u.lang = idioma === "en" ? "en-US" : "es-MX";
    const voz = vozLocal(idioma);
    if (voz) u.voice = voz;
    u.onstart = () => setHablando(true);
    u.onend = u.onerror = () => setHablando(false);
    window.speechSynthesis.speak(u);
  }

  function cerrar() { callar(); setAbierta(false); setRespuesta(null); setAviso(""); }

  const grabando = fase === "grabando";
  const procesando = fase === "procesando";
  const etiquetaBoton = grabando ? t("boton.detener") : procesando ? t("boton.procesando") : t("boton.hablar");
  const esIA = respuesta?.fuente !== undefined && respuesta.fuente !== "reglas_locales";

  return (
    <div ref={contenedor} className="voz">
      {abierta && (
        <div className={`voz-panel${grabando ? " grabando" : procesando ? " procesando" : hablando ? " hablando" : ""}`} role="dialog" aria-label={t("titulo")} aria-live="polite">
          <div className="voz-cab">
            <div className="voz-titulo">
              <span className={`voz-punto${grabando ? " grabando" : procesando ? " procesando" : hablando ? " hablando" : " activo"}`} aria-hidden="true" />
              <strong>{t("titulo")}</strong>
            </div>
            <button type="button" className="ghost icono" onClick={cerrar} aria-label={t("cerrar")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </div>
          {grabando && (
            <div className="voz-escena grabando">
              <div className="voz-mic-orbe" aria-hidden="true">
                <span className="voz-mic-halo" />
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg>
              </div>
              <div className="voz-escena-info">
                <span className="voz-onda" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /></span>
                <p className="voz-estado">{t("estado.escuchando")}</p>
              </div>
            </div>
          )}
          {procesando && (
            <div className="voz-escena procesando">
              <div className="voz-orbita" aria-hidden="true"><span /></div>
              <div className="voz-escena-info">
                <span className="voz-onda asistente pensando" aria-hidden="true"><i /><i /><i /><i /><i /></span>
                <p className="voz-estado">{t("estado.procesando")}</p>
              </div>
            </div>
          )}
          {aviso && <p className="voz-aviso" role="alert">{aviso}</p>}
          {respuesta && (
            <>
              {respuesta.transcripcion && <p className="voz-tu"><span>{t("tu")}</span>{respuesta.transcripcion}</p>}
              <div className={`voz-resp-caja${hablando ? " hablando" : ""}`}>
                <p className="voz-resp">{respuesta.texto}</p>
                {hablando && (
                  <div className="voz-habla-barra" aria-hidden="true">
                    <span className="voz-onda asistente"><i /><i /><i /><i /><i /><i /><i /></span>
                  </div>
                )}
              </div>
              <p className="voz-ia">{esIA ? t("etiqueta.ia") : t("etiqueta.reglas")}</p>
              {(respuesta.audio_base64 || puedeHablar()) && (
                <button type="button" className={`ghost voz-repetir${hablando ? " hablando" : ""}`} onClick={() => reproducir(respuesta)} disabled={hablando}>
                  {hablando && <span className="voz-onda asistente mini" aria-hidden="true"><i /><i /><i /><i /></span>}
                  {hablando ? t("escuchando") : t("repetir")}
                </button>
              )}
            </>
          )}
          {!grabando && !procesando && !respuesta && !aviso && <p className="voz-estado">{t("ayuda")}</p>}
        </div>
      )}
      <button type="button" className={`voz-bola${abierta ? " abierta" : ""}${grabando ? " grabando" : ""}${procesando ? " procesando" : ""}${hablando ? " hablando" : ""}`}
        onClick={grabando ? detener : empezar} disabled={procesando} aria-label={etiquetaBoton} aria-pressed={grabando} title={etiquetaBoton}>
        <span className="voz-anillos" aria-hidden="true"><i /><i /></span>
        {grabando ? (
          <span className="voz-icono-activo" aria-hidden="true">
            <span className="voz-onda boton"><i /><i /><i /><i /><i /></span>
            <svg className="voz-stop" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="4" /></svg>
          </span>
        ) : hablando ? (
          <span className="voz-onda boton asistente" aria-hidden="true"><i /><i /><i /><i /><i /></span>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></svg>
        )}
      </button>
    </div>
  );
}
