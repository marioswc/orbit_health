import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";

type EstadoVoz = "inactivo" | "grabando" | "procesando" | "reproduciendo";
type RespuestaVoz = { transcripcion?: string; texto?: string; audio_base64?: string; audio_media_type?: string };

const DURACION_TURNO_MS = 8000;

function mimeAudio(): string {
  const opciones = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return opciones.find((tipo) => MediaRecorder.isTypeSupported(tipo)) ?? "";
}

function audioDesdeBase64(base64: string, tipo: string): HTMLAudioElement {
  const bytes = Uint8Array.from(atob(base64), (caracter) => caracter.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: tipo }));
  const audio = new Audio(url);
  audio.addEventListener("ended", () => URL.revokeObjectURL(url), { once: true });
  return audio;
}

export default function AsistenteVoz({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("bienestar");
  const [estado, setEstado] = useState<EstadoVoz>("inactivo");
  const [mensaje, setMensaje] = useState<{ ok: boolean; texto: string } | null>(null);
  const [ultimoTurno, setUltimoTurno] = useState<{ pregunta: string; respuesta: string } | null>(null);
  const grabadora = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const temporizador = useRef<number | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const conversacionActiva = useRef(false);

  const limpiarGrabacion = useCallback(() => {
    if (temporizador.current !== null) window.clearTimeout(temporizador.current);
    temporizador.current = null;
    stream.current?.getTracks().forEach((pista) => pista.stop());
    stream.current = null;
    grabadora.current = null;
  }, []);

  const iniciarTurno = useCallback(async () => {
    if (!conversacionActiva.current || estado !== "inactivo") return;
    setMensaje(null);
    try {
      const obtenido = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!conversacionActiva.current) {
        obtenido.getTracks().forEach((pista) => pista.stop());
        return;
      }
      const tipo = mimeAudio();
      const nueva = tipo ? new MediaRecorder(obtenido, { mimeType: tipo }) : new MediaRecorder(obtenido);
      const partes: Blob[] = [];
      stream.current = obtenido;
      grabadora.current = nueva;
      nueva.ondataavailable = (evento) => { if (evento.data.size) partes.push(evento.data); };
      nueva.onstop = () => {
        limpiarGrabacion();
        if (!partes.length) {
          setEstado("inactivo");
          setMensaje({ ok: false, texto: t("voz.noAudio") });
          return;
        }
        void enviarTurno(new Blob(partes, { type: nueva.mimeType || "audio/webm" }), nueva.mimeType || "audio/webm");
      };
      nueva.start();
      setEstado("grabando");
      temporizador.current = window.setTimeout(() => nueva.stop(), DURACION_TURNO_MS);
    } catch (error) {
      setEstado("inactivo");
      setMensaje({ ok: false, texto: error instanceof DOMException && error.name === "NotAllowedError" ? t("voz.micDenied") : t("voz.unavailable") });
    }
  }, [estado, limpiarGrabacion, t]);

  const enviarTurno = useCallback(async (grabacion: Blob, tipo: string) => {
    setEstado("procesando");
    try {
      const resultado = await api<RespuestaVoz>(`/voz/chat/${tripulanteId}`, {
        method: "POST",
        headers: { "Content-Type": tipo.split(";", 1)[0] || "audio/webm" },
        body: grabacion,
      });
      setUltimoTurno({ pregunta: resultado.transcripcion ?? "", respuesta: resultado.texto ?? "" });
      if (!resultado.audio_base64) {
        setEstado("inactivo");
        if (conversacionActiva.current) void iniciarTurno();
        return;
      }
      const siguiente = audioDesdeBase64(resultado.audio_base64, resultado.audio_media_type ?? "audio/wav");
      audio.current = siguiente;
      siguiente.onended = () => {
        audio.current = null;
        setEstado("inactivo");
        if (conversacionActiva.current) void iniciarTurno();
      };
      setEstado("reproduciendo");
      await siguiente.play();
    } catch (error) {
      setEstado("inactivo");
      setMensaje({ ok: false, texto: error instanceof Error ? error.message : t("voz.error") });
    }
  }, [iniciarTurno, t, tripulanteId]);

  const detenerTurno = () => {
    if (grabadora.current?.state === "recording") grabadora.current.stop();
  };

  const finalizar = () => {
    conversacionActiva.current = false;
    if (grabadora.current?.state === "recording") grabadora.current.stop();
    else limpiarGrabacion();
    audio.current?.pause();
    audio.current = null;
    setEstado("inactivo");
  };

  const iniciar = () => {
    conversacionActiva.current = true;
    void iniciarTurno();
  };

  useEffect(() => finalizar, [limpiarGrabacion]);

  return (
    <section className="tarjeta pieza asistente-voz" aria-label={t("voz.aria")}>
      <div className="pieza-cab">
        <div><h2>{t("voz.title")}</h2><p className="suave">{t("voz.hint")}</p></div>
        <span className={`badge ${estado === "grabando" ? "amarillo" : estado === "inactivo" ? "sin_datos" : "verde"}`}>
          {t(`voz.status.${estado}`)}
        </span>
      </div>
      <div className="voz-controles">
        {estado === "inactivo" && <button type="button" className="btn-primario" onClick={iniciar}>{t("voz.start")}</button>}
        {estado === "grabando" && <button type="button" className="btn-primario" onClick={detenerTurno}>{t("voz.send")}</button>}
        {(estado === "procesando" || estado === "reproduciendo") && <button type="button" disabled>{t(`voz.status.${estado}`)}</button>}
        {estado !== "inactivo" && <button type="button" className="ghost" onClick={finalizar}>{t("voz.end")}</button>}
      </div>
      {ultimoTurno && <div className="voz-turno"><p><strong>{t("voz.you")}:</strong> {ultimoTurno.pregunta}</p><p><strong>{t("voz.assistant")}:</strong> {ultimoTurno.respuesta}</p></div>}
      {mensaje && <Alerta tono={mensaje.ok ? "ok" : "error"}>{mensaje.texto}</Alerta>}
    </section>
  );
}
