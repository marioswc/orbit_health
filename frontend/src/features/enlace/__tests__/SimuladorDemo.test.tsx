import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SimuladorDemo from "../components/SimuladorDemo";

describe("SimuladorDemo", () => {
  it("muestra la comparativa con y sin ORBIT y los escenarios disponibles", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const u = String(url);
      if (u.includes("/demo/escenarios")) {
        return new Response(JSON.stringify([{ id: "hipoxia_eclipse", descripcion: "Hipoxia con eclipse", pasos: 7 }]), { status: 200 });
      }
      return new Response(JSON.stringify({
        entorno: "marte",
        retardo_unidireccional_s: 1200,
        respuesta_tierra_min: 1,
        evento: "SpO₂ 88 %",
        tipo: "ilustracion",
        aviso: "Narración con supuestos.",
        ventana_sin_apoyo_s: 2460,
        ventana_sin_apoyo_min: 41,
        con_orbit: [{ t_s: 0, t_demo_s: 0, texto: "Clasificado a bordo" }],
        sin_orbit: [{ t_s: 2460, t_demo_s: 4.1, texto: "Llega respuesta de Tierra" }],
      }), { status: 200 });
    }));

    render(<SimuladorDemo />);
    expect(await screen.findByText(/El dilema de la latencia: SpO₂ 88 %/)).toBeInTheDocument();
    expect(screen.getByText("Con ORBIT a bordo")).toBeInTheDocument();
    expect(screen.getByText("Sin ORBIT")).toBeInTheDocument();
    expect(screen.getByText("hipoxia eclipse")).toBeInTheDocument();
  });
});

