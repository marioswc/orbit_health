import { describe, expect, it } from "vitest";
import type { LecturaEstado } from "../types/estado";
import { compararConBase, formatoDelta } from "../utils/lineaBase";
import { nombreIndicador } from "../utils/indicadores";

const base = (valor: number, lb?: LecturaEstado["linea_base"]): LecturaEstado => ({ indicador: "frecuencia_cardiaca", valor, unidad: "lpm", nivel: "verde", ts: "", linea_base: lb });

describe("compararConBase", () => {
  it("sin linea_base o sin muestras suficientes no hay comparacion", () => {
    expect(compararConBase(base(80)).disponible).toBe(false);
    const c = compararConBase(base(80, { aplica: false, n: 3, aviso: false }));
    expect(c.disponible).toBe(false);
    expect(c.muestras).toBe(3);
  });
  it("calcula la diferencia y la tendencia contra la media", () => {
    const sube = compararConBase(base(88, { aplica: true, n: 20, aviso: true, media: 68, desviacion: 4, z: 5 }));
    expect(sube).toMatchObject({ disponible: true, media: 68, delta: 20, tendencia: "↑", desvio: true });
    expect(compararConBase(base(60, { aplica: true, n: 20, aviso: false, media: 68, desviacion: 4, z: -2 })).tendencia).toBe("↓");
  });
  it("una diferencia chica frente a la variacion habitual se muestra estable", () => {
    expect(compararConBase(base(69, { aplica: true, n: 20, aviso: false, media: 68, desviacion: 4, z: 0.25 })).tendencia).toBe("→");
  });
  it("con desviacion cero, cualquier cambio cuenta y la igualdad es estable", () => {
    expect(compararConBase(base(70, { aplica: true, n: 10, aviso: true, media: 68, desviacion: 0, z: null })).tendencia).toBe("↑");
    expect(compararConBase(base(68, { aplica: true, n: 10, aviso: false, media: 68, desviacion: 0, z: null })).tendencia).toBe("→");
  });
  it("el desvio lo decide el backend (aviso), no se recalcula", () => {
    expect(compararConBase(base(200, { aplica: true, n: 10, aviso: false, media: 68, desviacion: 4, z: 33 })).desvio).toBe(false);
  });
});

describe("formatoDelta", () => {
  it("antepone + a los positivos y limita a un decimal", () => {
    expect(formatoDelta(20)).toBe("+20");
    expect(formatoDelta(-3.46)).toBe("-3.5");
    expect(formatoDelta(0)).toBe("0");
  });
});

describe("nombreIndicador", () => {
  it("usa nombres conocidos y humaniza el resto", () => {
    expect(nombreIndicador("spo2")).toBe("SpO₂");
    expect(nombreIndicador("algo_nuevo")).toBe("Algo nuevo");
  });
});

