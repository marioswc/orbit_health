import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Tamizaje from "../components/Tamizaje";

describe("Tamizaje y protocolo de crisis con calidad de oxígeno", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("permite abrir el protocolo de crisis considerando calidad de oxígeno y avisar al comandante con consentimiento", async () => {
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const ruta = String(url);
      if (ruta.includes("/crisis/protocolo")) {
        return new Response(
          JSON.stringify({
            nivel: "crisis",
            titulo: "Protocolo de crisis psicológica y seguridad a bordo",
            urgencia: "inmediata",
            tono: "directo",
            pasos: [
              "Verifica de inmediato la calidad de oxígeno en cabina (O₂: 18.5 %, nivel rojo) y mide tu SpO₂.",
              "No permanezcas a solas: acude ahora a un módulo común.",
            ],
            calidad_oxigeno: {
              presente: true,
              valor_pct: 18.5,
              nivel: "rojo",
              alerta: true,
              causa: "hipoxia_ambiental",
            },
            contactos_abordo: [{ rol: "comandante", etiqueta: "Comandante o un compañero de confianza" }],
            permite_aviso_medico: true,
            privado: true,
            transmitido_tierra: false,
            estado_validacion: "pendiente_validacion_salud_mental",
            aviso: "Supuesto de diseño pendiente de validación.",
            capsulas: [{ id: "crisis-anclaje", titulo: "Anclaje inmediato 5-4-3-2-1", contenido_markdown: "Nombra 5 cosas." }],
          }),
          { status: 200 },
        );
      }
      if (ruta.includes("/crisis/aviso-medico") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            id: 7,
            tripulante_id: "T1",
            tipo: "crisis",
            nivel_protocolo: "crisis",
            tamizaje_id: null,
            mensaje_opcional: null,
            estado: "pendiente",
            atendido_por: null,
            creado_ts: "2026-11-14T12:00:00Z",
          }),
          { status: 200 },
        );
      }
      if (ruta.includes("/crisis/avisos/7/revocar") && init?.method === "POST") {
        return new Response(
          JSON.stringify({
            id: 7,
            tripulante_id: "T1",
            tipo: "crisis",
            nivel_protocolo: "crisis",
            tamizaje_id: null,
            mensaje_opcional: null,
            estado: "revocado",
            atendido_por: null,
            creado_ts: "2026-11-14T12:00:00Z",
          }),
          { status: 200 },
        );
      }
      return new Response("{}", { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Tamizaje tripulanteId="T1" />);
    fireEvent.change(screen.getByLabelText(/Calidad de oxígeno en cabina/), { target: { value: "18.5" } });
    fireEvent.click(screen.getByRole("button", { name: "Protocolo de crisis" }));

    expect(await screen.findByText("Protocolo de crisis psicológica y seguridad a bordo")).toBeInTheDocument();
    expect(screen.getByText(/Calidad de oxígeno en cabina: 18.5 %/)).toBeInTheDocument();
    expect(screen.getByText("Anclaje inmediato 5-4-3-2-1")).toBeInTheDocument();

    const botonAvisar = screen.getByRole("button", { name: "Avisar al comandante con mi consentimiento" });
    expect(botonAvisar).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/Autorizo avisar al comandante/));
    expect(botonAvisar).not.toBeDisabled();
    fireEvent.click(botonAvisar);

    expect(await screen.findByText("Aviso compartido con el comandante")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Revocar consentimiento" }));
    await waitFor(() =>
      expect(screen.getByText(/Consentimiento revocado/)).toBeInTheDocument(),
    );
  });
});
