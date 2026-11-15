import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import InstalarApp from "../components/InstalarApp";
import { iniciarPwa } from "../pwa";

function eventoInstalar(resultado: "accepted" | "dismissed" = "accepted") {
  const e = new Event("beforeinstallprompt", { cancelable: true }) as Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };
  e.prompt = vi.fn(async () => undefined);
  e.userChoice = Promise.resolve({ outcome: resultado });
  return e;
}

describe("App instalable", () => {
  beforeEach(() => { vi.stubGlobal("matchMedia", (q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} })); });
  afterEach(() => vi.unstubAllGlobals());

  it("no muestra nada hasta que el navegador permite instalar", () => {
    iniciarPwa();
    const { container } = render(<InstalarApp />);
    expect(container).toBeEmptyDOMElement();
  });

  it("ofrece instalar cuando el navegador lo permite, y al aceptar llama a prompt() y desaparece", async () => {
    iniciarPwa();
    render(<InstalarApp />);
    const ev = eventoInstalar();
    act(() => { window.dispatchEvent(ev); });
    expect(ev.defaultPrevented).toBe(true);                               // se guarda para mostrarlo en el momento oportuno
    const boton = await screen.findByRole("button", { name: "Instalar" });
    await act(async () => { fireEvent.click(boton); });
    expect(ev.prompt).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Instalar" })).not.toBeInTheDocument();
  });

  it("'Ahora no' lo oculta sin instalar", async () => {
    iniciarPwa();
    render(<InstalarApp />);
    act(() => { window.dispatchEvent(eventoInstalar()); });
    fireEvent.click(await screen.findByRole("button", { name: "Ahora no" }));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
