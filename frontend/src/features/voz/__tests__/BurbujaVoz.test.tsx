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
});
