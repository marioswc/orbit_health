import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RachaMediciones from "../components/RachaMediciones";

describe("RachaMediciones", () => {
  it("muestra la racha actual, faltantes de hoy y logros", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
      racha_dias: 3,
      mejor_racha_dias: 4,
      dias_completos: 5,
      hoy_completo: false,
      hoy_faltan: ["SpO₂"],
      logros: [{ id: "tres_dias", nombre: "Tres días seguidos", logrado: true }],
      regla: "La racha no se rompe mientras el día de hoy esté en curso.",
    }), { status: 200 })));

    render(<RachaMediciones tripulanteId="T1" estado={null} />);
    expect(await screen.findByText(/3 días seguidos/)).toBeInTheDocument();
    expect(screen.getByText(/Hoy faltan: SpO₂/)).toBeInTheDocument();
    expect(screen.getByText(/✓ Tres días seguidos/)).toBeInTheDocument();
  });
});

