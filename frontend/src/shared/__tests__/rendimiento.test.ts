import { afterEach, describe, expect, it } from "vitest";
import { LIMITE_MS, aplicarNivel, debeDegradar, degradar, detectarNivel, nivelActual } from "../rendimiento";

describe("detectarNivel", () => {
  it("equipo potente: alto", () => expect(detectarNivel({ memoriaGb: 8, nucleos: 8 })).toBe("alto"));
  it("equipo modesto: medio", () => expect(detectarNivel({ memoriaGb: 4, nucleos: 4 })).toBe("medio"));
  it("equipo muy modesto: bajo", () => {
    expect(detectarNivel({ memoriaGb: 2, nucleos: 8 })).toBe("bajo");
    expect(detectarNivel({ memoriaGb: 8, nucleos: 2 })).toBe("bajo");
  });
  it("ahorro de datos: bajo", () => expect(detectarNivel({ memoriaGb: 8, nucleos: 8, ahorroDatos: true })).toBe("bajo"));
  it("sin datos del equipo: alto (no penaliza lo que no se puede medir)", () => expect(detectarNivel({})).toBe("alto"));
  it("la URL manda sobre todo", () => {
    expect(detectarNivel({ forzado: "1", memoriaGb: 16, nucleos: 16 })).toBe("bajo");
    expect(detectarNivel({ forzado: "0", memoriaGb: 1 })).toBe("alto");
    expect(detectarNivel({ forzado: "medio", memoriaGb: 16 })).toBe("medio");
  });
  it("lo guardado manda sobre la deteccion", () => expect(detectarNivel({ guardado: "bajo", memoriaGb: 16, nucleos: 16 })).toBe("bajo"));
  it("ignora valores invalidos", () => expect(detectarNivel({ forzado: "turbo", guardado: "x", memoriaGb: 8, nucleos: 8 })).toBe("alto"));
});

describe("degradar y debeDegradar", () => {
  it("baja un escalon y se detiene en bajo", () => {
    expect(degradar("alto")).toBe("medio");
    expect(degradar("medio")).toBe("bajo");
    expect(degradar("bajo")).toBe("bajo");
  });
  it("degrada solo si el promedio supera el limite del nivel", () => {
    expect(debeDegradar("alto", LIMITE_MS.alto - 1)).toBe(false);
    expect(debeDegradar("alto", LIMITE_MS.alto + 1)).toBe(true);
    expect(debeDegradar("medio", 41)).toBe(true);
    expect(debeDegradar("bajo", 5000)).toBe(false); // no hay donde bajar
  });
});

describe("aplicarNivel", () => {
  afterEach(() => { delete document.documentElement.dataset.rendimiento; localStorage.clear(); });
  it("fija data-rendimiento y lo lee nivelActual", () => {
    expect(nivelActual()).toBe("alto");
    aplicarNivel("medio");
    expect(document.documentElement.dataset.rendimiento).toBe("medio");
    expect(nivelActual()).toBe("medio");
  });
  it("solo recuerda cuando se pide", () => {
    aplicarNivel("bajo");
    expect(localStorage.getItem("orbit-rendimiento")).toBeNull();
    aplicarNivel("bajo", true);
    expect(localStorage.getItem("orbit-rendimiento")).toBe("bajo");
  });
});
