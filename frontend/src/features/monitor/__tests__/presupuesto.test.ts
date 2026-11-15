import { describe, expect, it } from "vitest";

// Presupuesto de peso de los SVG. Si crece, correr `pnpm --ignore-workspace optimizar:svg` antes de subir.
const LIMITE_POR_ARCHIVO = 300 * 1024;
const LIMITE_TOTAL = 600 * 1024;

const crudos = import.meta.glob<string>("../assets/*.svg", { query: "?raw", import: "default", eager: true });
const rasters = import.meta.glob("../assets/*.webp", { query: "?url", import: "default", eager: true });
const tamanos = Object.entries(crudos).map(([ruta, texto]) => ({ nombre: ruta.split("/").pop()!, bytes: new Blob([texto]).size }));

describe("presupuesto de assets", () => {
  it("estan las 4 capas (esqueleto y musculos son imagenes WebP (organos sigue siendo un SVG))", () => {
    expect(tamanos.map((t) => t.nombre).sort()).toEqual(["astronauta.svg", "organos.svg"]);
    expect(Object.keys(rasters).map((r) => r.split("/").pop())).toEqual(["esqueleto.webp", "musculos.webp"]);
  });
  it("ningun SVG pasa de 300 KB", () => {
    for (const t of tamanos) expect(t.bytes, t.nombre).toBeLessThan(LIMITE_POR_ARCHIVO);
  });
  it("el total no pasa de 600 KB", () => {
    expect(tamanos.reduce((s, t) => s + t.bytes, 0)).toBeLessThan(LIMITE_TOTAL);
  });
});
