import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import VistaTierra from "../components/VistaTierra";

describe("VistaTierra", () => {
  it("muestra mensajes recibidos en Tierra y enlaces de descarga del informe", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).includes("/tierra/mensajes")) {
        return new Response(JSON.stringify({
          timestamp_tierra: "2026-11-14T19:00:00Z",
          recibidos: [{ id: 1, tripulante_id: "T1", tipo_evento: "LECTURA_SPO2", prioridad: 1 }],
        }), { status: 200 });
      }
      return new Response(JSON.stringify({
        generado_ts: "2026-11-14T19:00:00Z",
        aviso: "No incluye diario ni ánimo.",
        tripulacion: [{ id: "T1", nombre: "Tripulante Uno", rol: "Comandante", nivel_general: "rojo", news2: { puntos: 5, nivel: "rojo" } }],
      }), { status: 200 });
    }));

    render(<VistaTierra />);
    expect(await screen.findByText("Lectura spo2")).toBeInTheDocument();
    expect(screen.getByText("Tripulante Uno")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CSV T1" })).toHaveAttribute("href", "/api/informe/T1?formato=csv");
  });
});

