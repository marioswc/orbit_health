import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import BarraSuperior from "../BarraSuperior";
import BotonCaptura from "../BotonCaptura";
import { nombreIndicador } from "../../features/monitor/utils/nombreIndicador";
import ConsolaEnlace, { textoTipo } from "../../features/enlace/components/ConsolaEnlace";


const base = { vista: "monitor" as const, alCambiarVista: vi.fn(), tema: "light" as const, alAlternarTema: vi.fn(), selector: <span>selector</span> };

describe("BotonCaptura", () => {
  it("abre la captura manual y se deshabilita sin tripulante", async () => {
    const alAbrir = vi.fn();
    const { rerender } = render(<BotonCaptura alAbrir={alAbrir} disponible />);
    await userEvent.click(screen.getByRole("button", { name: "Captura manual" }));
    expect(alAbrir).toHaveBeenCalled();
    rerender(<BotonCaptura alAbrir={alAbrir} disponible={false} />);
    expect(screen.getByRole("button", { name: "Captura manual" })).toBeDisabled();
  });
});

describe("BarraSuperior", () => {
  it("marca la vista actual y cambia de vista", async () => {
    const alCambiarVista = vi.fn();
    render(<BarraSuperior {...base} alCambiarVista={alCambiarVista} />);
    expect(screen.getByRole("button", { name: "Monitor" })).toHaveAttribute("aria-current", "page");
    await userEvent.click(screen.getByRole("button", { name: "Enlace" }));
    expect(alCambiarVista).toHaveBeenCalledWith("enlace");
  });
  it("incluye el selector de tripulante", () => {
    render(<BarraSuperior {...base} />);
    expect(screen.getByText("selector")).toBeInTheDocument();
  });
});

describe("nombres legibles", () => {
  it("indicadores conocidos y desconocidos", () => {
    expect(nombreIndicador("spo2")).toBe("SpO₂");
    expect(nombreIndicador("frecuencia_cardiaca")).toBe("Frec. cardiaca");
    expect(nombreIndicador("nueva_medida")).toBe("Nueva medida");
  });
  it("tipos de evento de la cola", () => {
    expect(textoTipo("LECTURA_PRESION_DIASTOLICA")).toBe("Lectura presion diastolica");
  });
});

describe("ConsolaEnlace", () => {
  const cola = (activo: boolean) => ({
    enlace: { activo, entorno: "luna" }, resumen: {},
    items: [
      { id: 1, tripulante_id: "T1", tipo_evento: "LECTURA_SPO2", prioridad: 1, estado: "retenido", hash: "h1" },
      { id: 2, tripulante_id: "T1", tipo_evento: "LECTURA_TEMP", prioridad: 3, estado: "recibido", hash: "h2" },
    ],
  });
  beforeEach(() => { vi.useRealTimers(); });
  afterEach(() => vi.unstubAllGlobals());

  it("muestra conteos por estado, columnas por prioridad y estado del enlace", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => cola(true) }));
    render(<ConsolaEnlace />);
    expect(await screen.findByText("Enlace activo")).toBeInTheDocument();
    expect(screen.getByText("Lectura spo2")).toBeInTheDocument();
    expect(screen.getByText("Sin eventos")).toBeInTheDocument(); // prioridad 2 vacia
    expect(screen.getByRole("radio", { name: "Luna · 1.3 s" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Enlace normal" })).toBeChecked();
  });
  it("en modo Eclipse avisa que nada sale", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => cola(false) }));
    render(<ConsolaEnlace />);
    expect(await screen.findByText(/Eclipse: nada sale/)).toBeInTheDocument();
  });
});
