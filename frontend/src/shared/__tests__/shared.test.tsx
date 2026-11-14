import { act, render, renderHook, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api, post } from "../api/client";
import Selector from "../components/Selector";
import Contador from "../components/Contador";
import { useTema } from "../hooks/useTema";

const OPC = [{ valor: "a", etiqueta: "Alfa" }, { valor: "b", etiqueta: "Beta" }, { valor: "c", etiqueta: "Gamma" }];

describe("Selector", () => {
  it("abre, elige con clic y cierra", async () => {
    const alCambiar = vi.fn();
    render(<Selector opciones={OPC} valor="a" alCambiar={alCambiar} etiqueta="Letra" />);
    const caja = screen.getByRole("combobox", { name: "Letra" });
    expect(caja).toHaveTextContent("Alfa");
    await userEvent.click(caja);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("option", { name: "Beta" }));
    expect(alCambiar).toHaveBeenCalledWith("b");
    expect(screen.queryByRole("listbox")).toBeNull();
  });
  it("navega con flechas, elige con Enter y cierra con Escape", async () => {
    const alCambiar = vi.fn();
    render(<Selector opciones={OPC} valor="a" alCambiar={alCambiar} etiqueta="Letra" />);
    screen.getByRole("combobox").focus();
    await userEvent.keyboard("{ArrowDown}{ArrowDown}{ArrowDown}{Enter}");
    expect(alCambiar).toHaveBeenCalledWith("c");
    await userEvent.keyboard("{ArrowDown}");
    expect(screen.getByRole("listbox")).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).toBeNull();
  });
  it("muestra el marcador si no hay valor elegido", () => {
    render(<Selector opciones={OPC} valor="" alCambiar={() => {}} etiqueta="Letra" marcador="Elige" />);
    expect(screen.getByRole("combobox")).toHaveTextContent("Elige");
  });
});

describe("Contador", () => {
  it("con reduced-motion salta directo al valor", () => {
    vi.spyOn(window, "matchMedia").mockReturnValue({ matches: true } as MediaQueryList);
    const { rerender } = render(<Contador valor={3} />);
    expect(screen.getByText("3")).toBeInTheDocument();
    rerender(<Contador valor={7} />);
    expect(screen.getByText("7")).toBeInTheDocument();
  });
});

describe("api client", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("api devuelve el JSON y usa el prefijo /api", async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ x: 1 }) });
    vi.stubGlobal("fetch", f);
    expect(await api<{ x: number }>("/ping")).toEqual({ x: 1 });
    expect(f.mock.calls[0][0]).toBe("/api/ping");
  });
  it("lanza el detalle del backend cuando hay error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 422, statusText: "Unprocessable", json: async () => ({ detail: "valor fuera de rango" }) }));
    await expect(api("/x")).rejects.toThrow("valor fuera de rango");
  });
  it("sin cuerpo JSON usa estado y texto HTTP", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, statusText: "Boom", json: async () => { throw new Error("no json"); } }));
    await expect(api("/x")).rejects.toThrow("500 Boom");
  });
  it("post envia JSON con metodo POST", async () => {
    const f = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", f);
    await post("/enlace", { activo: true });
    expect(f.mock.calls[0][1]).toMatchObject({ method: "POST", body: JSON.stringify({ activo: true }) });
  });
});

describe("useTema", () => {
  afterEach(() => { delete document.documentElement.dataset.theme; localStorage.clear(); });
  it("alterna y persiste el tema", () => {
    document.documentElement.dataset.theme = "light";
    const { result } = renderHook(() => useTema());
    expect(result.current.tema).toBe("light");
    act(() => result.current.alternar());
    expect(result.current.tema).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("orbit-tema")).toBe("dark");
  });
});
