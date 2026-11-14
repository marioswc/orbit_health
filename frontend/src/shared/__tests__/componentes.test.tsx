import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import Drawer from "../components/Drawer";
import Segmentado from "../components/Segmentado";
import EncabezadoPagina from "../components/EncabezadoPagina";

const OPC = [{ valor: "a", etiqueta: "Alfa" }, { valor: "b", etiqueta: "Beta" }, { valor: "c", etiqueta: "Gamma" }];

describe("Drawer", () => {
  it("no renderiza nada cerrado", () => {
    render(<Drawer abierto={false} alCerrar={() => {}} titulo="Captura">contenido</Drawer>);
    expect(screen.queryByRole("dialog")).toBeNull();
  });
  it("abierto es un dialogo modal con titulo accesible y foco en el primer campo", () => {
    render(<Drawer abierto alCerrar={() => {}} titulo="Captura"><input aria-label="valor" /></Drawer>);
    const d = screen.getByRole("dialog", { name: "Captura" });
    expect(d).toHaveAttribute("aria-modal", "true");
    expect(screen.getByLabelText("valor")).toHaveFocus();
  });
  it("Escape, boton cerrar y clic en el fondo lo cierran", () => {
    const alCerrar = vi.fn();
    const { container } = render(<Drawer abierto alCerrar={alCerrar} titulo="Captura"><input aria-label="valor" /></Drawer>);
    fireEvent.keyDown(document, { key: "Escape" });
    fireEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    fireEvent.mouseDown(document.querySelector(".drawer-fondo")!);
    expect(alCerrar).toHaveBeenCalledTimes(3);
    expect(container).toBeEmptyDOMElement(); // se monta en un portal
  });
  it("el foco vuelve al elemento que abrio el cuadro", async () => {
    function Prueba() {
      const [a, setA] = useState(false);
      return <><button onClick={() => setA(true)}>abrir</button><Drawer abierto={a} alCerrar={() => setA(false)} titulo="T"><input aria-label="x" /></Drawer></>;
    }
    render(<Prueba />);
    const abrir = screen.getByText("abrir");
    abrir.focus();
    await userEvent.click(abrir);
    expect(screen.getByLabelText("x")).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(abrir).toHaveFocus();
  });
  it("Tab no sale del dialogo", async () => {
    render(<Drawer abierto alCerrar={() => {}} titulo="T"><input aria-label="uno" /><input aria-label="dos" /></Drawer>);
    await userEvent.tab(); // uno -> dos
    await userEvent.tab(); // dos -> (envuelve) cerrar
    expect(screen.getByRole("button", { name: "Cerrar" })).toHaveFocus();
  });
});

describe("Segmentado", () => {
  it("expone radiogroup con la opcion elegida", () => {
    render(<Segmentado opciones={OPC} valor="b" alCambiar={() => {}} etiqueta="Letra" />);
    expect(screen.getByRole("radiogroup", { name: "Letra" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Beta" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Alfa" })).not.toBeChecked();
  });
  it("clic y flechas cambian la opcion (con vuelta al inicio)", async () => {
    const alCambiar = vi.fn();
    render(<Segmentado opciones={OPC} valor="c" alCambiar={alCambiar} etiqueta="Letra" />);
    await userEvent.click(screen.getByRole("radio", { name: "Alfa" }));
    expect(alCambiar).toHaveBeenLastCalledWith("a");
    screen.getByRole("radio", { name: "Gamma" }).focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(alCambiar).toHaveBeenLastCalledWith("a");
    await userEvent.keyboard("{ArrowLeft}");
    expect(alCambiar).toHaveBeenLastCalledWith("c"); // desde Alfa, la flecha izquierda vuelve al final
  });
  it("sin valor, la primera opcion es alcanzable con Tab", () => {
    render(<Segmentado opciones={OPC} valor="" alCambiar={() => {}} etiqueta="Letra" />);
    expect(screen.getByRole("radio", { name: "Alfa" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("radio", { name: "Beta" })).toHaveAttribute("tabindex", "-1");
  });
});

describe("EncabezadoPagina", () => {
  it("muestra etiqueta, titulo, descripcion y contenido lateral", () => {
    render(<EncabezadoPagina etiqueta="Enlace" titulo="Enlace con la Tierra" descripcion="Qué sale"><span>activo</span></EncabezadoPagina>);
    expect(screen.getByRole("heading", { level: 1, name: "Enlace con la Tierra" })).toBeInTheDocument();
    expect(screen.getByText("Enlace")).toBeInTheDocument();
    expect(screen.getByText("activo")).toBeInTheDocument();
  });
});
