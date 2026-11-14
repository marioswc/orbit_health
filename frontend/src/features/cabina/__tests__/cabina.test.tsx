import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MonitorCabina from "../components/MonitorCabina";
import { resolverAmbiente } from "../utils/ambiente";
import type { AlertasColectivas } from "../types/cabina";

const colectivas = (extra: Partial<AlertasColectivas> = {}): AlertasColectivas => ({ alertas: [], co2_mmhg: null, niveles: {}, ...extra });

describe("resolverAmbiente", () => {
  it("sin datos no inventa nivel", () => {
    expect(resolverAmbiente(null, null, null)).toEqual({ co2: null, co2Nivel: null, dosis: null, nivel: "sin_datos" });
  });
  it("toma el CO2 del cruce colectivo y el nivel del backend cuando lo informa", () => {
    const a = resolverAmbiente(colectivas({ co2_mmhg: 3.6, co2_nivel: "amarillo" }), null, null);
    expect(a).toMatchObject({ co2: 3.6, co2Nivel: "amarillo", nivel: "amarillo" });
  });
  it("usa el nivel de la lectura del tripulante solo si es el mismo valor", () => {
    expect(resolverAmbiente(colectivas({ co2_mmhg: 3.6 }), { valor: 3.6, nivel: "amarillo" }, null).co2Nivel).toBe("amarillo");
    expect(resolverAmbiente(colectivas({ co2_mmhg: 4.2 }), { valor: 3.6, nivel: "amarillo" }, null).co2Nivel).toBeNull();
  });
  it("el nivel de cabina es el peor entre CO2 y dosis", () => {
    const a = resolverAmbiente(colectivas({ co2_mmhg: 2.8, co2_nivel: "verde" }), null, { valor: 92, nivel: "rojo" });
    expect(a.nivel).toBe("rojo");
  });
});

describe("MonitorCabina", () => {
  it("muestra CO2 con su nivel y descripcion, y la dosis con medidor", () => {
    const ambiente = resolverAmbiente(colectivas({ co2_mmhg: 3.6, co2_nivel: "amarillo" }), null, { valor: 42, nivel: "verde" });
    render(<MonitorCabina ambiente={ambiente} alerta={null} />);
    expect(screen.getByText("3.6")).toBeInTheDocument();
    expect(screen.getByText("Saturación parcial de filtros")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: /Dosis/ })).toHaveAttribute("aria-valuenow", "42");
  });
  it("sin lecturas lo dice y no muestra medidores falsos", () => {
    render(<MonitorCabina ambiente={resolverAmbiente(null, null, null)} alerta={null} />);
    expect(screen.getByText("Sin lectura reciente de CO₂.")).toBeInTheDocument();
    expect(screen.getByText("Sin lectura reciente de dosis.")).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).toBeNull();
  });
  it("si no hay nivel de CO2, lo avisa en vez de pintarlo", () => {
    render(<MonitorCabina ambiente={resolverAmbiente(colectivas({ co2_mmhg: 3.6 }), null, null)} alerta={null} />);
    expect(screen.getByText(/no informó el nivel/)).toBeInTheDocument();
  });
  it("la alerta colectiva aparece como aviso con texto", () => {
    const alerta = { id: "a", nombre: "CO2 de cabina elevado con varios tripulantes afectados", nivel: "rojo" as const, afectados: 2, co2_mmhg: 3.6 };
    render(<MonitorCabina ambiente={resolverAmbiente(null, null, null)} alerta={alerta} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/2 tripulantes afectados/);
  });
});

