import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnilloNews2, PulsoCardiaco, SignosVitales, num } from "../components/TableroSignos";
import type { LecturaEstado } from "../types/estado";

const fc: LecturaEstado = { indicador: "frecuencia_cardiaca", valor: 104, unidad: "lpm", nivel: "amarillo", ts: "2026-11-14T10:00:00Z" };
const temp: LecturaEstado = { indicador: "temperatura", valor: 37.599999999999994, unidad: "°C", nivel: "verde", ts: "2026-11-14T10:00:00Z" };

describe("TableroSignos", () => {
  it("num evita decimales de mas", () => expect(num(37.599999999999994)).toBe(37.6));

  it("el anillo NEWS2 expone el puntaje real", () => {
    render(<AnilloNews2 puntos={5} nivel="amarillo" ventana={60} />);
    expect(screen.getByRole("img", { name: "Puntaje NEWS2: 5" })).toBeInTheDocument();
    expect(screen.getByText("Ventana de 60 min")).toBeInTheDocument();
  });

  it("el pulso late a la frecuencia registrada y sin dato no inventa", () => {
    const { rerender, container } = render(<PulsoCardiaco lectura={fc} />);
    expect(screen.getByText("104")).toBeInTheDocument();
    expect((container.querySelector(".corazon-latido") as SVGElement).style.getPropertyValue("--lat")).toBe("0.58s");
    rerender(<PulsoCardiaco />);
    expect(screen.getByText("Sin frecuencia cardíaca reciente")).toBeInTheDocument();
  });

  it("los signos muestran valores redondeados y permiten elegir uno", () => {
    const elegidos: string[] = [];
    render(<SignosVitales vitales={[fc, temp]} series={{}} seleccionado="temperatura" alElegir={(c) => elegidos.push(c)} />);
    expect(screen.getByText(/37\.6/)).toBeInTheDocument();
    screen.getByRole("button", { name: /Frec\. card/ }).click();
    expect(elegidos).toEqual(["frecuencia_cardiaca"]);
    expect(screen.getByRole("button", { name: /Temper/ })).toHaveAttribute("aria-pressed", "true");
  });

  it("sin lecturas lo dice", () => {
    render(<SignosVitales vitales={[]} series={{}} seleccionado={null} alElegir={() => {}} />);
    expect(screen.getByText(/Aún no hay lecturas/)).toBeInTheDocument();
  });
});
