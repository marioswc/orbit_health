import { StrictMode } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import BurbujaVoz from "../components/BurbujaVoz";
import { changeLanguage } from "../../../i18n";

/** MediaRecorder minimo para jsdom: al detenerse entrega un trozo de audio y dispara onstop. */
class GrabadorFalso {
  static isTypeSupported = () => true;
  mimeType = "audio/webm";
  state: "inactive" | "recording" = "inactive";
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  start() { this.state = "recording"; }
  stop() {
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob([new Uint8Array(2000)], { type: "audio/webm" }) });
    this.onstop?.();
  }
}

describe("BurbujaVoz", () => {
  afterEach(async () => {
    await changeLanguage("es");
    vi.unstubAllGlobals();
  });

  it("envia el audio y sale de 'procesando' aunque StrictMode monte el componente dos veces", async () => {
    const pista = { stop: vi.fn() };
    vi.stubGlobal("MediaRecorder", GrabadorFalso);
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn(async () => ({ getTracks: () => [pista] })) },
    });
    const fetchMock = vi.fn(async () => new Response(
      JSON.stringify({ texto: "Tu nivel es verde.", transcripcion: "¿Cómo estoy?", fuente: "reglas_locales" }),
      { status: 200 },
    ));
    vi.stubGlobal("fetch", fetchMock);
    const speak = vi.fn((u: { onstart?: (() => void) | null }) => { u.onstart?.(); });
    vi.stubGlobal("SpeechSynthesisUtterance", class { lang = ""; voice = null; onstart: (() => void) | null = null; onend: (() => void) | null = null; onerror: (() => void) | null = null; constructor(public text: string) {} });
    vi.stubGlobal("speechSynthesis", { speak, cancel: vi.fn(), getVoices: () => [] });

    const { container } = render(<StrictMode><BurbujaVoz tripulanteId="T1" /></StrictMode>);
    const boton = screen.getByRole("button", { pressed: false });
    await act(async () => { fireEvent.click(boton); });
    expect(container.querySelector(".voz-escena.grabando")).toBeInTheDocument();
    expect(screen.getByRole("button", { pressed: true })).toHaveClass("grabando");

    await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: true })); });

    await waitFor(() => expect(screen.getByText("Tu nivel es verde.")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith("/api/voz/chat/T1?idioma=es", expect.objectContaining({ method: "POST" }));
    expect(screen.getByRole("button", { pressed: false })).not.toBeDisabled();
    expect(screen.getByRole("button", { pressed: false })).toHaveClass("hablando");
    expect(container.querySelector(".voz-resp-caja.hablando")).toBeInTheDocument();
    // Sin audio de Piper, la respuesta se lee con la voz local del sistema
    expect(speak).toHaveBeenCalledWith(expect.objectContaining({ text: "Tu nivel es verde.", lang: "es-MX" }));
  });

  it("envia el idioma ingles y usa una voz inglesa en el fallback local", async () => {
    await changeLanguage("en");
    const pista = { stop: vi.fn() };
    vi.stubGlobal("MediaRecorder", GrabadorFalso);
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn(async () => ({ getTracks: () => [pista] })) },
    });
    const fetchMock = vi.fn(async () => new Response(
      JSON.stringify({ texto: "Your level is green.", transcripcion: "How am I?", idioma: "en", fuente: "reglas_locales" }),
      { status: 200 },
    ));
    vi.stubGlobal("fetch", fetchMock);
    const speak = vi.fn((u: { onstart?: (() => void) | null }) => { u.onstart?.(); });
    vi.stubGlobal("SpeechSynthesisUtterance", class { lang = ""; voice = null; onstart: (() => void) | null = null; onend: (() => void) | null = null; onerror: (() => void) | null = null; constructor(public text: string) {} });
    vi.stubGlobal("speechSynthesis", { speak, cancel: vi.fn(), getVoices: () => [] });

    render(<BurbujaVoz tripulanteId="T1" />);
    await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
    await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: true })); });

    await waitFor(() => expect(screen.getByText("Your level is green.")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith("/api/voz/chat/T1?idioma=en", expect.objectContaining({ method: "POST" }));
    expect(speak).toHaveBeenCalledWith(expect.objectContaining({ text: "Your level is green.", lang: "en-US" }));
  });

  it("conserva el turno anterior en el hilo al hacer una segunda pregunta", async () => {
    vi.stubGlobal("MediaRecorder", GrabadorFalso);
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn(async () => ({ getTracks: () => [{ stop: vi.fn() }] })) },
    });
    const respuestas = [
      { texto: "Primera respuesta.", transcripcion: "Primera pregunta", fuente: "reglas_locales" },
      { texto: "Segunda respuesta.", transcripcion: "Segunda pregunta", fuente: "reglas_locales" },
    ];
    let n = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) =>
      String(url).includes("/voz/estado")
        ? new Response(JSON.stringify({ lista: true, motivo: "lista", detalle: "La voz está lista." }), { status: 200 })
        : new Response(JSON.stringify(respuestas[n++]), { status: 200 })));
    vi.stubGlobal("speechSynthesis", undefined);

    const { container } = render(<BurbujaVoz tripulanteId="T1" />);
    const turno = async () => {
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: true })); });
    };
    await turno();
    await waitFor(() => expect(screen.getByText("Primera respuesta.")).toBeInTheDocument());
    expect(container.querySelector(".voz-hilo")).toBeNull();

    await turno();
    await waitFor(() => expect(screen.getByText("Segunda respuesta.")).toBeInTheDocument());
    const hilo = container.querySelector(".voz-hilo");
    expect(hilo).toBeInTheDocument();
    expect(hilo).toHaveTextContent("Primera pregunta");
    expect(hilo).toHaveTextContent("Primera respuesta.");
  });

  describe("cuando la voz no está disponible dice QUÉ falta, no un error genérico", () => {
    const preparar = (estado: object | null, chat: Response | null = null) => {
      const getUserMedia = vi.fn(async () => ({ getTracks: () => [{ stop: vi.fn() }] }));
      vi.stubGlobal("MediaRecorder", GrabadorFalso);
      Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
      vi.stubGlobal("speechSynthesis", undefined);
      vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
        if (String(url).includes("/voz/estado")) return estado ? new Response(JSON.stringify(estado), { status: 200 }) : new Response("{}", { status: 404 });
        return chat ?? new Response(JSON.stringify({ texto: "Hola", transcripcion: "hola", fuente: "reglas_locales" }), { status: 200 });
      }));
      return getUserMedia;
    };

    it("faltan las librerías: lo explica y no pide el micrófono", async () => {
      const getUserMedia = preparar({ lista: false, motivo: "faltan_librerias", detalle: "x" });
      render(<BurbujaVoz tripulanteId="T1" />);
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
      expect(await screen.findByRole("alert")).toHaveTextContent(/Faltan las librerías de voz/);
      expect(getUserMedia).not.toHaveBeenCalled();
    });

    it("voz apagada: manda a escribirle a Nova en vez de decir que configure variables", async () => {
      preparar({ lista: false, motivo: "desactivada", detalle: "x" });
      render(<BurbujaVoz tripulanteId="T1" />);
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
      const aviso = await screen.findByRole("alert");
      expect(aviso).toHaveTextContent(/pestaña Asistente/);
    });

    it("un 503 al enviar el audio vuelve a preguntar el motivo real", async () => {
      let consultas = 0;
      preparar(null);
      vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
        if (String(url).includes("/voz/estado")) {
          consultas++;
          return new Response(JSON.stringify(consultas === 1 ? { lista: true, motivo: "lista", detalle: "" } : { lista: false, motivo: "modelo_no_existe", detalle: "x" }), { status: 200 });
        }
        return new Response("{}", { status: 503 });
      }));
      render(<BurbujaVoz tripulanteId="T1" />);
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: true })); });
      expect(await screen.findByRole("alert")).toHaveTextContent(/modelo de reconocimiento de voz no está/);
    });

    it("si el backend no tiene el aviso de estado (404), igual intenta grabar", async () => {
      const getUserMedia = preparar(null);
      render(<BurbujaVoz tripulanteId="T1" />);
      await act(async () => { fireEvent.click(screen.getByRole("button", { pressed: false })); });
      await waitFor(() => expect(getUserMedia).toHaveBeenCalled());
    });
  });
});
