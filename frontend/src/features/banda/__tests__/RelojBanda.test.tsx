import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RelojBanda from "../components/RelojBanda";

describe("RelojBanda", () => {
  it("muestra las lecturas reales y las describe para lectores de pantalla", () => {
    render(<RelojBanda fc={104} spo2={93} news2={{ puntos: 5, nivel: "amarillo" }} signosHoy={3} simulada />);
    expect(screen.getByRole("img", { name: /frecuencia cardíaca 104 lpm, SpO₂ 93 %, 3 de 5/ })).toBeInTheDocument();
    expect(screen.getByText("104")).toBeInTheDocument();
    expect(screen.getByText("3/5")).toBeInTheDocument();
    expect(screen.getByText("NEWS2 5")).toBeInTheDocument();
    expect(screen.getByText("SIM")).toBeInTheDocument();
  });

  it("sin lecturas no inventa valores", () => {
    const { container } = render(<RelojBanda signosHoy={0} simulada={false} />);
    expect(screen.getAllByText("—").length).toBe(2);
    expect(screen.queryByText("SIM")).toBeNull();
    expect(container.querySelector(".reloj-corazon")).toBeNull();
  });

  it("el corazon late a la frecuencia registrada", () => {
    const { container } = render(<RelojBanda fc={120} signosHoy={1} simulada={false} />);
    expect((container.querySelector(".reloj-corazon") as SVGElement).style.getPropertyValue("--lat")).toBe("0.50s");
  });

  it("cambia de pantalla con la corona, los puntos y el teclado", () => {
    render(<RelojBanda fc={104} spo2={93} news2={{ puntos: 5, nivel: "amarillo" }} ventana={60} signosHoy={3} simulada={false} />);
    const grupo = screen.getByRole("group", { name: /Reloj de la banda en 3D, pantalla Anillos \(1 de 5\)/ });
    fireEvent.click(screen.getByRole("button", { name: "Corona: siguiente pantalla" }));
    expect(screen.getByRole("group", { name: /pantalla Pulso \(2 de 5\)/ })).toBeInTheDocument();
    fireEvent.keyDown(grupo, { key: "ArrowRight" });
    expect(screen.getByRole("group", { name: /pantalla Oxígeno \(3 de 5\)/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Misión" }));
    expect(screen.getByRole("group", { name: /pantalla Misión \(5 de 5\)/ })).toBeInTheDocument();
    fireEvent.keyDown(grupo, { key: "ArrowLeft" });
    expect(screen.getByRole("group", { name: /pantalla NEWS2 \(4 de 5\)/ })).toBeInTheDocument();
  });

  it("la pantalla de mision no inventa: sin mision lo dice", () => {
    render(<RelojBanda signosHoy={0} simulada={false} />);
    fireEvent.click(screen.getByRole("tab", { name: "Misión" }));
    expect(screen.getByText(/Sin misión en curso/)).toBeInTheDocument();
  });
});
