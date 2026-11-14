import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import DetalleZona from "../components/DetalleZona";

describe("DetalleZona", () => {
  it("sin lecturas muestra el aviso y el estado sin datos", () => {
    render(<DetalleZona id="resp" lecturas={[]} capa="traje" meses={0} alMeses={() => {}} />);
    expect(screen.getByText("sin datos")).toBeInTheDocument();
    expect(screen.getByText(/Sin lecturas recientes de: spo2/)).toBeInTheDocument();
  });
  it("muestra el valor y nivel de los indicadores de la zona", () => {
    render(<DetalleZona id="resp" lecturas={[{ indicador: "spo2", valor: 88, unidad: "%", nivel: "rojo", ts: "" }]} capa="traje" meses={0} alMeses={() => {}} />);
    expect(screen.getByText("88 %")).toBeInTheDocument();
    expect(screen.getAllByText("rojo").length).toBeGreaterThan(0);
  });
  it("el control de meses solo sale en hueso de brazos/piernas y reporta la perdida", () => {
    const alMeses = vi.fn();
    const { rerender } = render(<DetalleZona id="brazos" lecturas={[]} capa="musculo" meses={0} alMeses={alMeses} />);
    expect(screen.queryByRole("slider")).toBeNull();
    rerender(<DetalleZona id="brazos" lecturas={[]} capa="hueso" meses={6} alMeses={alMeses} />);
    expect(screen.getByText("6–9 %")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("slider"), { target: { value: "3" } });
    expect(alMeses).toHaveBeenCalledWith(3);
  });
  it("zona inexistente no renderiza nada", () => {
    const { container } = render(<DetalleZona id="x" lecturas={[]} capa="traje" meses={0} alMeses={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
});
