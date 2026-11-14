import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RecordatorioCaptura from "../components/RecordatorioCaptura";

describe("RecordatorioCaptura", () => {
  it("muestra aviso cuando la captura esta vencida", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      if (String(url).endsWith("/recordatorios")) {
        return new Response(JSON.stringify({ vencidos: 2, tripulacion: [] }), { status: 200 });
      }
      return new Response(JSON.stringify({
        tripulante_id: "T1",
        nivel_general: "amarillo",
        intervalo_min: 15,
        vencido: true,
        sin_capturas: false,
        atrasado_min: 12.5,
        faltan_en_min: 0,
        faltantes_news2: ["avpu"],
      }), { status: 200 });
    }));

    render(<RecordatorioCaptura tripulanteId="T1" estado={null} />);
    expect(await screen.findByText(/Captura vencida hace 12\.5 min/)).toBeInTheDocument();
    expect(screen.getByText(/Faltantes NEWS2: avpu/)).toBeInTheDocument();
  });
});

