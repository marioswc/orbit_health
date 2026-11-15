import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import AsistenteLocal from "../components/AsistenteLocal";
import type { Estado } from "../types/estado";

const ESTADO: Estado = {
  ventana_min: 15,
  nivel_general: "amarillo",
  nivel_fisiologico: "amarillo",
  news2: { puntos: 2, nivel: "amarillo", faltantes: [] },
  indicadores: [],
  reglas_combinadas: [],
  acciones_sugeridas: [],
  proxima_captura_min: 15,
  peligros_relacionados: [],
};

describe("AsistenteLocal", () => {
  afterEach(() => vi.restoreAllMocks());

  it("muestra la explicacion con etiqueta IA local y aviso cuando viene de modelo local", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          fuente: "modelo_local",
          modelo: "qwen2.5:3b",
          generado_por_ia: true,
          aviso: "Texto generado por un modelo local. No es un diagnóstico y no modifica la alerta.",
          explicacion: "El estado es amarillo por frecuencia respiratoria elevada.",
          nivel_general: "amarillo",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<AsistenteLocal tripulanteId="c1" estado={ESTADO} />);

    await waitFor(() => {
      expect(screen.getByText(/El estado es amarillo por frecuencia respiratoria elevada\./)).toBeInTheDocument();
    });
    expect(screen.getByText("IA local · qwen2.5:3b")).toBeInTheDocument();
    expect(screen.getByText(/No es un diagnóstico/)).toBeInTheDocument();
  });

  it("muestra respaldo de reglas locales cuando no hay modelo activo", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          fuente: "reglas_locales",
          modelo: null,
          generado_por_ia: false,
          explicacion: "El estado general es amarillo según las reglas configuradas.",
          nivel_general: "amarillo",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    render(<AsistenteLocal tripulanteId="c1" estado={ESTADO} />);

    await waitFor(() => {
      expect(screen.getByText("Reglas locales")).toBeInTheDocument();
    });
    expect(screen.getByText(/reglas configuradas/)).toBeInTheDocument();
  });
});
