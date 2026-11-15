import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import AsistenteFlotante from "../AsistenteFlotante";
import type { Estado } from "../../features/monitor/types/estado";

const ESTADO: Estado = {
  ventana_min: 15,
  nivel_general: "verde",
  nivel_fisiologico: "verde",
  news2: { puntos: 0, nivel: "verde", faltantes: [] },
  indicadores: [],
};

describe("AsistenteFlotante", () => {
  afterEach(() => vi.restoreAllMocks());

  it("abre el panel al pulsar el boton flotante y muestra el resumen de IA local", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          fuente: "modelo_local",
          modelo: "qwen2.5:3b",
          generado_por_ia: true,
          aviso: "Texto generado por un modelo local. No es un diagnóstico y no modifica la alerta.",
          explicacion: "Todo en verde según las lecturas actuales.",
          nivel_general: "verde",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<AsistenteFlotante tripulanteId="elena" estado={ESTADO} />);
    await userEvent.click(screen.getByRole("button", { name: "Asistente local" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog", { name: "Asistente local ORBIT" })).toBeInTheDocument();
      expect(screen.getByText(/Todo en verde según las lecturas actuales\./)).toBeInTheDocument();
    });
    expect(screen.getByText("IA local · qwen2.5:3b")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hablar" })).toBeInTheDocument();
  });
});
