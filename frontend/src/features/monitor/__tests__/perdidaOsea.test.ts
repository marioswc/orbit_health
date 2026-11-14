import { describe, expect, it } from "vitest";
import { MESES_MAX, perdidaOsea, textoPerdida } from "../utils/perdidaOsea";

describe("perdidaOsea", () => {
  it("0 meses = 0 %", () => {
    expect(perdidaOsea(0)).toEqual({ min: 0, max: 0 });
    expect(textoPerdida(0)).toBe("0 %");
  });
  it("usa 1-1.5 % por mes", () => {
    expect(perdidaOsea(6)).toEqual({ min: 6, max: 9 });
    expect(textoPerdida(6)).toBe("6–9 %");
    expect(textoPerdida(1)).toBe("1–1.5 %");
  });
  it("acota meses fuera de rango", () => {
    expect(perdidaOsea(-3)).toEqual({ min: 0, max: 0 });
    expect(perdidaOsea(99)).toEqual(perdidaOsea(MESES_MAX));
  });
});
