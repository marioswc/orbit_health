import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { registrarEspanol } from "../../../i18n";
import esAsistente from "../../../i18n/locales/ES/features/asistente/asistente.json";
import ChatAsistente from "../components/ChatAsistente";

registrarEspanol("asistente", esAsistente);

interface Llamada { ruta: string; metodo: string; cuerpo?: string }

function simular(respuestaChat: object) {
  const llamadas: Llamada[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const ruta = String(url);
    llamadas.push({ ruta, metodo: init?.method ?? "GET", cuerpo: init?.body as string | undefined });
    if (ruta.includes("/asistente/saludo/")) return new Response(JSON.stringify({ texto: "Hola Camila, soy Nova.", sugerencias: ["Me siento solo", "Quiero respirar"] }), { status: 200 });
    if (ruta.includes("/perfil-ia/")) return new Response(JSON.stringify({ intereses: init?.method === "PUT" ? JSON.parse(String(init.body)).intereses : "la astronomía", rasgos: "tranquila" }), { status: 200 });
    if (ruta.includes("/asistente/chat/")) return new Response(JSON.stringify(respuestaChat), { status: 200 });
    return new Response("{}", { status: 404 });
  }));
  return llamadas;
}

describe("Nova, la compañía de apoyo", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("saluda por su nombre y ofrece atajos para empezar", async () => {
    simular({});
    render(<ChatAsistente tripulanteId="T3" />);
    expect(await screen.findByText(/Hola Camila, soy Nova\./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Me siento solo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quiero respirar" })).toBeInTheDocument();
  });

  it("un atajo envía el mensaje, muestra la respuesta con su aviso de IA y manda el historial reciente", async () => {
    const llamadas = simular({ texto: "Te escucho. ¿Qué extrañas hoy?", fuente: "modelo_local", generado_por_ia: true, aviso: "Texto generado por un modelo local." });
    render(<ChatAsistente tripulanteId="T3" />);
    fireEvent.click(await screen.findByRole("button", { name: "Me siento solo" }));
    expect(await screen.findByText(/Te escucho\. ¿Qué extrañas hoy\?/)).toBeInTheDocument();
    expect(screen.getByText("Texto generado por un modelo local.")).toBeInTheDocument();
    const chat = llamadas.find((l) => l.ruta.includes("/asistente/chat/T3"))!;
    expect(chat.metodo).toBe("POST");
    const cuerpo = JSON.parse(chat.cuerpo!);
    expect(cuerpo.texto).toBe("Me siento solo");
    expect(cuerpo.historial).toEqual([{ rol: "asistente", texto: "Hola Camila, soy Nova." }]);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Me siento solo" })).not.toBeInTheDocument());   // los atajos se van tras empezar
  });

  it("si la respuesta viene de reglas, lo dice y no la presenta como IA", async () => {
    simular({ texto: "Recibí tu mensaje.", fuente: "reglas_locales", generado_por_ia: false });
    render(<ChatAsistente tripulanteId="T3" />);
    fireEvent.change(await screen.findByLabelText(/Escribe aquí/), { target: { value: "hola" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(/sin IA generativa/)).toBeInTheDocument();
  });

  it("la guía de respiración (texto escrito) no se marca como IA", async () => {
    simular({ texto: "Vamos a respirar juntos.", fuente: "guia_respiracion", generado_por_ia: false });
    render(<ChatAsistente tripulanteId="T3" />);
    fireEvent.click(await screen.findByRole("button", { name: "Quiero respirar" }));
    expect(await screen.findByText(/Vamos a respirar juntos\./)).toBeInTheDocument();
    expect(screen.queryByText(/sin IA generativa/)).not.toBeInTheDocument();
  });

  it("guarda lo que cuentas de ti al salir del campo", async () => {
    const llamadas = simular({});
    render(<ChatAsistente tripulanteId="T3" />);
    const intereses = await screen.findByLabelText(/Qué te gusta/);
    fireEvent.change(intereses, { target: { value: "el ajedrez" } });
    fireEvent.blur(intereses);
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "PUT" && l.ruta.includes("/perfil-ia/T3"))).toBe(true));
  });
});
