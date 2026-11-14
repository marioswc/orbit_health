import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import FiguraHumana, { estiloCamara } from "../components/FiguraHumana";
import type { LecturaEstado } from "../types/estado";

const props = { lecturas: [] as LecturaEstado[], seleccionada: "cardio", acercado: false, capa: "traje" as const, meses: 0, alSeleccionar: vi.fn(), alAlejar: vi.fn() };

describe("FiguraHumana", () => {
  it("expone una zona clicable por region con su estado", () => {
    render(<FiguraHumana {...props} lecturas={[{ indicador: "spo2", valor: 80, unidad: "%", nivel: "rojo", ts: "" }]} />);
    expect(screen.getAllByRole("button").length).toBe(6);
    expect(screen.getByRole("button", { name: /Respiratorio: rojo/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cardiovascular: sin datos/ })).toBeInTheDocument();
  });
  it("clic y teclado seleccionan la zona", () => {
    const alSeleccionar = vi.fn();
    render(<FiguraHumana {...props} alSeleccionar={alSeleccionar} />);
    const resp = screen.getByRole("button", { name: /Respiratorio/ });
    fireEvent.click(resp);
    fireEvent.keyDown(resp, { key: "Enter" });
    expect(alSeleccionar).toHaveBeenCalledTimes(2);
    expect(alSeleccionar).toHaveBeenCalledWith("resp");
  });
  it("el boton de ver cuerpo completo solo aparece al acercar", () => {
    const alAlejar = vi.fn();
    const { rerender } = render(<FiguraHumana {...props} />);
    expect(screen.queryByText("Ver cuerpo completo")).toBeNull();
    rerender(<FiguraHumana {...props} acercado alAlejar={alAlejar} />);
    fireEvent.click(screen.getByText("Ver cuerpo completo"));
    expect(alAlejar).toHaveBeenCalled();
  });
  it("las flechas solo aparecen en capas de anatomia y se filtran por zona al acercar", () => {
    const { container, rerender } = render(<FiguraHumana {...props} capa="traje" />);
    expect(container.querySelectorAll(".flecha").length).toBe(0);
    rerender(<FiguraHumana {...props} capa="organos" />);
    expect(container.querySelectorAll(".flecha").length).toBe(5);
    rerender(<FiguraHumana {...props} capa="organos" acercado seleccionada="cardio" />);
    expect(container.querySelectorAll(".flecha").length).toBe(1);
    expect(screen.getByText("Corazón")).toBeInTheDocument();
  });
  it("solo monta las capas visitadas (carga perezosa)", () => {
    const { container, rerender } = render(<FiguraHumana {...props} capa="traje" />);
    expect(container.querySelectorAll(".capa-grupo").length).toBe(0);
    rerender(<FiguraHumana {...props} capa="hueso" />);
    expect(container.querySelectorAll(".capa-grupo").length).toBe(1);
    rerender(<FiguraHumana {...props} capa="organos" />);
    expect(container.querySelectorAll(".capa-grupo").length).toBe(2);
  });
});

describe("estiloCamara", () => {
  it("sin acercar no transforma", () => {
    expect(estiloCamara("cardio", "traje", false).transform).toBe("none");
  });
  it("al acercar escala con el zoom de la zona", () => {
    const e = estiloCamara("cardio", "organos", true);
    expect(String(e.transform)).toMatch(/scale\(2\.3\)/);
    expect(String(e.transformOrigin)).toMatch(/%/);
  });
});
