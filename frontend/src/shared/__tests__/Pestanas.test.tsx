import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Pestanas from "../components/Pestanas";

function Demo() {
  const [v, setV] = useState("a");
  return (
    <Pestanas etiqueta="Secciones" valor={v} alCambiar={setV} pestanas={[{ id: "a", etiqueta: "Uno" }, { id: "b", etiqueta: "Dos" }, { id: "c", etiqueta: "Tres" }]}>
      <p>contenido {v}</p>
    </Pestanas>
  );
}

describe("Pestanas", () => {
  it("muestra solo el contenido de la pestana activa y marca la seleccionada", () => {
    render(<Demo />);
    expect(screen.getByRole("tab", { name: "Uno" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("contenido a");
    fireEvent.click(screen.getByRole("tab", { name: "Dos" }));
    expect(screen.getByRole("tab", { name: "Dos" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("contenido b");
  });

  it("las flechas, Inicio y Fin mueven la seleccion (foco rotatorio)", () => {
    render(<Demo />);
    const uno = screen.getByRole("tab", { name: "Uno" });
    fireEvent.keyDown(uno, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Dos" })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: "Dos" }), { key: "End" });
    expect(screen.getByRole("tab", { name: "Tres" })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: "Tres" }), { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Uno" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Uno" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Dos" })).toHaveAttribute("tabindex", "-1");
  });
});
