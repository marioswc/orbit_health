import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PerfilMenu from "../components/PerfilMenu";

const props = { nombre: "Tripulante Uno", rol: "Comandante", id: "T1" };

describe("PerfilMenu", () => {
  it("muestra las iniciales y oculta el perfil hasta abrirlo", () => {
    render(<PerfilMenu {...props} alSalir={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Tripulante Uno/ })).toHaveTextContent("TU");
    expect(screen.queryByText("Comandante")).toBeNull();
  });

  it("al abrirlo muestra nombre, rol e id, y Salir cierra la sesion", () => {
    const alSalir = vi.fn();
    render(<PerfilMenu {...props} alSalir={alSalir} />);
    fireEvent.click(screen.getByRole("button", { name: /Tripulante Uno/ }));
    expect(screen.getByText("Comandante")).toBeInTheDocument();
    expect(screen.getByText("T1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Salir" }));
    expect(alSalir).toHaveBeenCalledTimes(1);
  });

  it("se cierra con Escape y al hacer clic fuera", () => {
    render(<><PerfilMenu {...props} alSalir={vi.fn()} /><p>fuera</p></>);
    const abrir = () => fireEvent.click(screen.getByRole("button", { name: /Tripulante Uno/ }));
    abrir();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("Comandante")).toBeNull();
    abrir();
    fireEvent.mouseDown(screen.getByText("fuera"));
    expect(screen.queryByText("Comandante")).toBeNull();
  });
});
