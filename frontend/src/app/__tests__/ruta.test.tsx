import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useRuta, vistaDeUrl } from "../useRuta";

describe("vistaDeUrl", () => {
  it("lee la ruta del hash", () => expect(vistaDeUrl({ hash: "#/historial", search: "" })).toBe("historial"));
  it("tolera #historial y subrutas", () => {
    expect(vistaDeUrl({ hash: "#sistema", search: "" })).toBe("sistema");
    expect(vistaDeUrl({ hash: "#/enlace/algo?x=1", search: "" })).toBe("enlace");
  });
  it("mantiene ?vista= como respaldo y el hash gana", () => {
    expect(vistaDeUrl({ hash: "", search: "?vista=riesgos" })).toBe("riesgos");
    expect(vistaDeUrl({ hash: "#/bienestar", search: "?vista=riesgos" })).toBe("bienestar");
  });
  it("una ruta desconocida cae en monitor", () => expect(vistaDeUrl({ hash: "#/nada", search: "" })).toBe("monitor"));
});

describe("useRuta", () => {
  afterEach(() => { window.location.hash = ""; document.title = ""; });

  it("cambia de vista, actualiza el hash y el titulo", async () => {
    const { result } = renderHook(() => useRuta());
    expect(result.current[0]).toBe("monitor");
    act(() => result.current[1]("historial"));
    expect(window.location.hash).toBe("#/historial");
    await waitFor(() => expect(result.current[0]).toBe("historial")); // hashchange llega de forma asincrona
    expect(document.title).toBe("Historial · ORBIT Health");
  });

  it("responde a cambios del hash (Atras/Adelante)", async () => {
    const { result } = renderHook(() => useRuta());
    await act(async () => { window.location.hash = "/enlace"; window.dispatchEvent(new HashChangeEvent("hashchange")); });
    expect(result.current[0]).toBe("enlace");
  });
});
