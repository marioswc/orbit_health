import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { registrarEspanol } from "../../../i18n";
import esAsistente from "../../../i18n/locales/ES/features/asistente/asistente.json";
import PerfilNova from "../components/PerfilNova";

registrarEspanol("asistente", esAsistente);

describe("PerfilNova", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("carga lo que Nova sabe de ti y lo guarda al salir del campo", async () => {
    const llamadas: { ruta: string; metodo: string }[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      llamadas.push({ ruta: String(url), metodo: init?.method ?? "GET" });
      const intereses = init?.method === "PUT" ? JSON.parse(String(init.body)).intereses : "la astronomía";
      return new Response(JSON.stringify({ intereses, rasgos: "tranquila" }), { status: 200 });
    }));
    render(<PerfilNova tripulanteId="T3" />);
    const campo = await screen.findByLabelText(/Qué te gusta/);
    await waitFor(() => expect(campo).toHaveValue("la astronomía"));
    fireEvent.change(campo, { target: { value: "el ajedrez" } });
    fireEvent.blur(campo);
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "PUT" && l.ruta.includes("/perfil-ia/T3"))).toBe(true));
    expect(await screen.findByText(/Guardado/)).toBeInTheDocument();
  });
});
