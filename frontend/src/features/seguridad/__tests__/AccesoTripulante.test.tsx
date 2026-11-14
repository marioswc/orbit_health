import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AccesoTripulante from "../components/AccesoTripulante";

describe("AccesoTripulante", () => {
  it("envia tripulante y PIN al iniciar sesion y permite cambiar a recuperacion", () => {
    const alEntrar = vi.fn().mockResolvedValue({});
    const alRecuperar = vi.fn().mockResolvedValue(undefined);
    render(
      <AccesoTripulante
        tripulantes={[{ valor: "T1", etiqueta: "Comandante" }]}
        alEntrar={alEntrar}
        alRecuperar={alRecuperar}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("6 a 10 dígitos"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(alEntrar).toHaveBeenCalledWith("T1", "123456");

    fireEvent.click(screen.getByRole("button", { name: "Recuperar PIN" }));
    expect(screen.getByPlaceholderText("Código entregado al alta")).toBeInTheDocument();
  });
});

