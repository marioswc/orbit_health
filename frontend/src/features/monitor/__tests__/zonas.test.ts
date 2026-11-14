import { describe, expect, it } from "vitest";
import { CAPAS, ZONAS, ancla, nivelZona } from "../zonas";
import { ZONA_PATHS } from "../zonasPaths";
import { CAJAS, REGIONES, VB, aFraccion, aPorcentaje } from "../components/ArteAstronauta";
import { ETIQUETAS, anguloFlecha, origenEtiqueta } from "../etiquetas";
import type { LecturaEstado } from "../types/estado";

const lectura = (indicador: string, nivel: LecturaEstado["nivel"]): LecturaEstado => ({ indicador, valor: 1, unidad: "u", nivel, ts: "2026-01-01T00:00:00Z" });
const dentro = (x: number, y: number) => x >= VB.x && x <= VB.x + VB.w && y >= VB.y && y <= VB.y + VB.h;

describe("nivelZona", () => {
  it("sin lecturas de la zona devuelve sin_datos", () => {
    expect(nivelZona(["spo2"], [])).toBe("sin_datos");
    expect(nivelZona(["spo2"], [lectura("otra", "rojo")])).toBe("sin_datos");
  });
  it("toma el peor nivel entre los indicadores de la zona", () => {
    const ls = [lectura("spo2", "verde"), lectura("frecuencia_respiratoria", "rojo"), lectura("otra", "verde")];
    expect(nivelZona(["spo2", "frecuencia_respiratoria"], ls)).toBe("rojo");
    expect(nivelZona(["spo2"], [lectura("spo2", "amarillo"), lectura("spo2", "verde")])).toBe("amarillo");
  });
});

describe("integridad de datos de zonas", () => {
  it("cada zona tiene trazo clicable, ancla dentro del dibujo y zoom razonable", () => {
    for (const z of ZONAS) {
      expect(ZONA_PATHS[z.id], `path de ${z.id}`).toBeTruthy();
      expect(z.zoom).toBeGreaterThan(1);
      for (const c of CAPAS) {
        const [x, y] = ancla(z, c.id);
        expect(dentro(x, y), `ancla ${z.id}/${c.id}`).toBe(true);
      }
    }
  });
  it("ids de zona unicos y capaInicial valida", () => {
    expect(new Set(ZONAS.map((z) => z.id)).size).toBe(ZONAS.length);
    for (const z of ZONAS) expect(CAPAS.map((c) => c.id)).toContain(z.capaInicial);
  });
  it("toda zona tiene region de recorte", () => {
    for (const z of ZONAS) expect(REGIONES[z.id]?.length, z.id).toBeGreaterThan(0);
  });
});

describe("geometria de capas", () => {
  it("aPorcentaje cubre el lienzo completo para la caja del traje", () => {
    expect(aPorcentaje(CAJAS.traje)).toEqual({ left: "0%", top: "0%", width: "100%", height: "100%" });
  });
  it("aFraccion devuelve fracciones de la caja de la capa", () => {
    const c = CAJAS.organos;
    expect(aFraccion([c[0], c[1], c[2] / 2, c[3] / 2], c)).toEqual([0, 0, 0.5, 0.5]);
  });
});

describe("etiquetas (flechas)", () => {
  const todas = Object.entries(ETIQUETAS).flatMap(([capa, es]) => (es ?? []).map((e) => ({ capa, e })));
  it("apuntan a una zona existente y caen dentro del dibujo", () => {
    expect(todas.length).toBeGreaterThan(10);
    for (const { capa, e } of todas) {
      expect(ZONAS.some((z) => z.id === e.zona), `${capa}/${e.texto}`).toBe(true);
      expect(dentro(e.tx, e.ty), `${e.texto} destino`).toBe(true);
      expect(dentro(e.lx, e.ly), `${e.texto} origen`).toBe(true);
    }
  });
  it("el origen cambia al acercar y el angulo apunta hacia el destino", () => {
    const e = ETIQUETAS.organos![0];
    expect(origenEtiqueta(e, false)).toEqual([e.lx, e.ly]);
    expect(origenEtiqueta(e, true)).not.toEqual([e.lx, e.ly]);
    expect(Math.abs(anguloFlecha(e, false))).toBeLessThan(90);
  });
});
