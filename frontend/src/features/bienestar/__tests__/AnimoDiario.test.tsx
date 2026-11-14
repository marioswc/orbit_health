import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AnimoDiario from "../components/AnimoDiario";

describe("AnimoDiario", () => {
  it("carga la serie, permite elegir un nivel y muestra la respuesta privada", async () => {
    const fetchMock = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === "POST") {
        return new Response(JSON.stringify({ valor: 2, bajo: true, aviso_linea_base: false, capsulas: [{ id: "c1", titulo: "Respiración", contenido_markdown: "Inhala 4 s" }], privado: true, transmitido_tierra: false }), { status: 200 });
      }
      return new Response(JSON.stringify({ puntos: [{ valor: 4, ts: "2026-11-14T08:00:00Z" }], media: 4, privado: true }), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AnimoDiario tripulanteId="T1" />);
    expect(await screen.findByLabelText(/Ánimo de los últimos 14 días, media 4/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Bajo" }));

    await waitFor(() => expect(screen.getByText("Respiración")).toBeInTheDocument());
  });
});

