import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import Bienvenida from "../components/Bienvenida";

describe("Guía de bienvenida", () => {
  beforeEach(() => localStorage.clear());

  it("se abre sola la primera vez y recorre los cinco pasos", () => {
    render(<Bienvenida />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Paso 1 de 5")).toBeInTheDocument();
    expect(screen.getByText("Bienvenido a ORBIT Health")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByText("El semáforo")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Atrás" }));
    expect(screen.getByText("Bienvenido a ORBIT Health")).toBeInTheDocument();
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByText("Paso 5 de 5")).toBeInTheDocument();
    expect(screen.getByText(/Simulado/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Siguiente" })).not.toBeInTheDocument();
  });

  it("al terminar o al omitir no vuelve a abrirse sola, y se puede reabrir con el botón de ayuda", () => {
    const { unmount } = render(<Bienvenida />);
    fireEvent.click(screen.getByRole("button", { name: "Omitir" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    unmount();
    render(<Bienvenida />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();       // ya la vio
    fireEvent.click(screen.getByRole("button", { name: "Guía de inicio" }));
    expect(screen.getByText("Paso 1 de 5")).toBeInTheDocument();         // empieza desde el principio
  });

  it("la tecla Escape la cierra y el último paso la termina", () => {
    render(<Bienvenida />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Guía de inicio" }));
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    fireEvent.click(screen.getByRole("button", { name: "Empezar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("dice con claridad que es un prototipo sin validación médica y que no hay IA que decida alertas", () => {
    render(<Bienvenida />);
    fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByText(/nunca lo decide una IA/)).toBeInTheDocument();
    for (let i = 0; i < 3; i++) fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(screen.getByText(/no sustituye a un médico/)).toBeInTheDocument();
  });
});
