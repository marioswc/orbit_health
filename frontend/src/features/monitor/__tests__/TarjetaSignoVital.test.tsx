import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import TarjetaSignoVital from "../components/TarjetaSignoVital";
import type { LecturaEstado } from "../types/estado";

const lectura = (extra: Partial<LecturaEstado> = {}): LecturaEstado => ({ indicador: "frecuencia_cardiaca", valor: 88, unidad: "lpm", nivel: "verde", ts: "t", ...extra });

describe("TarjetaSignoVital", () => {
  it("muestra valor, nivel y la comparacion con la linea base", () => {
    render(<TarjetaSignoVital lectura={lectura({ linea_base: { aplica: true, n: 20, aviso: true, media: 68, desviacion: 4, z: 5 } })} />);
    expect(screen.getByText("Frecuencia cardíaca")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText(/Tu línea base: 68 lpm \(\+20\)/)).toBeInTheDocument();
    expect(screen.getByText(/Desvío > 2σ/)).toBeInTheDocument();
  });
  it("el estado va siempre con texto, no solo con color", () => {
    render(<TarjetaSignoVital lectura={lectura({ nivel: "rojo" })} />);
    expect(screen.getByRole("article", { name: /rojo/ })).toBeInTheDocument();
    expect(screen.getByText("Fuera de rango")).toBeInTheDocument();
  });
  it("sin linea base suficiente lo dice claro y no inventa un valor", () => {
    render(<TarjetaSignoVital lectura={lectura({ linea_base: { aplica: false, n: 1, aviso: false } })} />);
    expect(screen.getByText(/Sin línea base suficiente \(1 lectura\)/)).toBeInTheDocument();
    expect(screen.getByText("Normal")).toBeInTheDocument();
  });
});

