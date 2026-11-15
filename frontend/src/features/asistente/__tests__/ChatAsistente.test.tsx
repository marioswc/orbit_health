import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { registrarEspanol } from "../../../i18n";
import esAsistente from "../../../i18n/locales/ES/features/asistente/asistente.json";
import ChatAsistente from "../components/ChatAsistente";

registrarEspanol("asistente", esAsistente);

describe("Chat con mi asistente", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("guarda los intereses, envía la pregunta y muestra la respuesta con su aviso de IA", async () => {
    const llamadas: { ruta: string; metodo: string; cuerpo?: string }[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const ruta = String(url);
      llamadas.push({ ruta, metodo: init?.method ?? "GET", cuerpo: init?.body as string | undefined });
      if (ruta.includes("/perfil-ia/")) return new Response(JSON.stringify({ intereses: init?.method === "PUT" ? JSON.parse(String(init.body)).intereses : "" }), { status: 200 });
      if (ruta.includes("/asistente/chat/")) {
        return new Response(JSON.stringify({ texto: "Hola, vas bien.", fuente: "modelo_local", generado_por_ia: true, aviso: "Texto generado por un modelo local." }), { status: 200 });
      }
      return new Response("{}", { status: 404 });
    }));

    render(<ChatAsistente tripulanteId="T3" />);
    const intereses = await screen.findByLabelText(/Qué te gusta/);
    fireEvent.change(intereses, { target: { value: "el ajedrez" } });
    fireEvent.blur(intereses);
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "PUT" && l.ruta.includes("/perfil-ia/T3"))).toBe(true));

    fireEvent.change(screen.getByLabelText(/Escribe aquí/), { target: { value: "hola" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(/Hola, vas bien\./)).toBeInTheDocument();
    expect(screen.getByText("Texto generado por un modelo local.")).toBeInTheDocument();
    const chat = llamadas.find((l) => l.ruta.includes("/asistente/chat/T3"));
    expect(chat?.metodo).toBe("POST");
    expect(JSON.parse(chat!.cuerpo!)).toEqual({ texto: "hola" });
  });

  it("si la respuesta viene de reglas, lo dice y no la presenta como IA", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL) => {
      const ruta = String(url);
      if (ruta.includes("/perfil-ia/")) return new Response(JSON.stringify({ intereses: "" }), { status: 200 });
      return new Response(JSON.stringify({ texto: "Recibí tu mensaje.", fuente: "reglas_locales", generado_por_ia: false }), { status: 200 });
    }));
    render(<ChatAsistente tripulanteId="T3" />);
    fireEvent.change(await screen.findByLabelText(/Escribe aquí/), { target: { value: "hola" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(/sin IA generativa/)).toBeInTheDocument();
  });
});
