import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DiarioTripulante from "../components/DiarioTripulante";

const ahora = Date.now();
const notaHace = (id: number, horas: number, contenido: string, titulo: string | null = null) =>
  ({ id, titulo, contenido, ts: new Date(ahora - horas * 3600e3).toISOString() });

function simular(notas = [notaHace(2, 1, "Hoy escribí cinco palabras aquí", "Hoy"), notaHace(1, 25, "Ayer también escribí algo", "Ayer")]) {
  vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    if (String(url).includes("/diario") && init?.method === "POST") return new Response("{}", { status: 200 });
    if (String(url).includes("/diario/")) return new Response(JSON.stringify(notas), { status: 200 });
    return new Response("{}", { status: 404 });
  }));
}

describe("DiarioTripulante", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it("el contador cuenta palabras al escribir", async () => {
    simular();
    render(<DiarioTripulante tripulanteId="T1" />);
    fireEvent.change(await screen.findByLabelText("Nota"), { target: { value: "una dos tres" } });
    expect(screen.getByText(/3 palabras/)).toBeInTheDocument();
  });

  it("guarda un borrador mientras escribes, lo recupera y lo borra al guardar la nota", async () => {
    simular();
    const { unmount } = render(<DiarioTripulante tripulanteId="T1" />);
    fireEvent.change(await screen.findByLabelText("Nota"), { target: { value: "borrador pendiente" } });
    await waitFor(() => expect(localStorage.getItem("orbit-diario-borrador-T1")).toContain("borrador pendiente"), { timeout: 2000 });
    unmount();

    render(<DiarioTripulante tripulanteId="T1" />);
    await waitFor(() => expect(screen.getByLabelText("Nota")).toHaveValue("borrador pendiente"));
    fireEvent.click(screen.getByRole("button", { name: "Guardar nota" }));
    await waitFor(() => expect(localStorage.getItem("orbit-diario-borrador-T1")).toBeNull());
  });

  it("el lector navega entre notas", async () => {
    simular();
    render(<DiarioTripulante tripulanteId="T1" />);
    fireEvent.click(await screen.findByRole("button", { name: /Ayer/ }));
    expect(await screen.findByText(/Ayer también escribí/, { selector: ".nota-lectura-texto" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Más reciente/ }));
    expect(await screen.findByText(/Hoy escribí cinco palabras/, { selector: ".nota-lectura-texto" })).toBeInTheDocument();
  });
});
