import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AccionesClinicas from "../components/AccionesClinicas";
import GraficaSerie from "../components/GraficaSerie";

describe("AccionesClinicas", () => {
  it("muestra la frecuencia recomendada, reglas combinadas activas y acciones sugeridas", () => {
    render(
      <AccionesClinicas
        nivel="amarillo"
        proximaCapturaMin={15}
        reglas={[{ id: "r1", nombre: "Pulso elevado con presión sistólica baja", nivel: "amarillo" }]}
        acciones={["Repetir medición en 15 min", "Revisar hidratación"]}
      />,
    );
    expect(screen.getByText(/Repetir medición cada 15 min/)).toBeInTheDocument();
    expect(screen.getByText("Pulso elevado con presión sistólica baja")).toBeInTheDocument();
    expect(screen.getByText("Revisar hidratación")).toBeInTheDocument();
  });
});

describe("GraficaSerie", () => {
  it("pinta la serie SVG con su resumen y permite cerrar", () => {
    const alCerrar = vi.fn();
    render(
      <GraficaSerie
        cargando={false}
        error=""
        alCerrar={alCerrar}
        serie={{
          indicador: "spo2",
          etiqueta: "SpO₂",
          unidad: "%",
          dias: 14,
          puntos: [
            { valor: 98, nivel: "verde", ts: "2026-11-14T10:00:00Z" },
            { valor: 93, nivel: "amarillo", ts: "2026-11-14T11:00:00Z" },
          ],
          resumen: { n: 2, min: 93, max: 98, media: 95.5 },
        }}
      />,
    );
    expect(screen.getByRole("img", { name: /Serie de SpO₂ con 2 puntos/ })).toBeInTheDocument();
    expect(screen.getByText(/mín 93 · media 95.5 · máx 98 %/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(alCerrar).toHaveBeenCalled();
  });
});

