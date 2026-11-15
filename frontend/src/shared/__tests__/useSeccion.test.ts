import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { seccionDeUrl, useSeccion } from "../hooks/useSeccion";

const SEC = ["animo", "diario", "apoyo"] as const;

describe("seccionDeUrl", () => {
  it("lee la seccion de #/bienestar/diario", () => expect(seccionDeUrl("#/bienestar/diario", "bienestar", SEC, "animo")).toBe("diario"));
  it("cae en la de por defecto si falta, no existe o es de otra vista", () => {
    expect(seccionDeUrl("#/bienestar", "bienestar", SEC, "animo")).toBe("animo");
    expect(seccionDeUrl("#/bienestar/nada", "bienestar", SEC, "animo")).toBe("animo");
    expect(seccionDeUrl("#/asistente/diario", "bienestar", SEC, "animo")).toBe("animo");
  });
  it("ignora parametros despues de ?", () => expect(seccionDeUrl("#/bienestar/apoyo?x=1", "bienestar", SEC, "animo")).toBe("apoyo"));
});

describe("useSeccion", () => {
  afterEach(() => { window.location.hash = ""; });

  it("empieza en la seccion de la URL y al cambiar actualiza el hash", () => {
    window.location.hash = "/bienestar/diario";
    const { result } = renderHook(() => useSeccion("bienestar", SEC, "animo"));
    expect(result.current[0]).toBe("diario");
    act(() => result.current[1]("apoyo"));
    expect(result.current[0]).toBe("apoyo");
    expect(window.location.hash).toBe("#/bienestar/apoyo");
  });

  it("responde a Atras/Adelante (cambio de hash) mientras la vista esta activa", async () => {
    window.location.hash = "/bienestar/animo";
    const { result } = renderHook(() => useSeccion("bienestar", SEC, "animo"));
    await act(async () => { window.location.hash = "/bienestar/diario"; window.dispatchEvent(new HashChangeEvent("hashchange")); });
    expect(result.current[0]).toBe("diario");
  });

  it("no reacciona si el hash ya es de otra vista", async () => {
    window.location.hash = "/bienestar/diario";
    const { result } = renderHook(() => useSeccion("bienestar", SEC, "animo"));
    await act(async () => { window.location.hash = "/sistema/auditoria"; window.dispatchEvent(new HashChangeEvent("hashchange")); });
    expect(result.current[0]).toBe("diario");
  });
});
