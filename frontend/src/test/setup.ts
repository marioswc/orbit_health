import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

if (typeof window.localStorage === "undefined") {
  const valores = new Map<string, string>();
  const almacenamiento = {
    getItem: (clave: string) => valores.get(clave) ?? null,
    setItem: (clave: string, valor: string) => { valores.set(clave, String(valor)); },
    removeItem: (clave: string) => { valores.delete(clave); },
    clear: () => { valores.clear(); },
    key: (indice: number) => Array.from(valores.keys())[indice] ?? null,
    get length() { return valores.size; },
  };
  Object.defineProperty(window, "localStorage", { configurable: true, value: almacenamiento });
  Object.defineProperty(globalThis, "localStorage", { configurable: true, value: almacenamiento });
}

// jsdom no trae matchMedia ni requestAnimationFrame estable en todos los casos
if (!window.matchMedia) {
  window.matchMedia = ((q: string) => ({ matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false })) as typeof window.matchMedia;
}

// jsdom no implementa scrollIntoView
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {};

// ApexCharts necesita SVG real (getBBox, ResizeObserver): en jsdom se sustituye por un marcador que conserva las opciones para poder inspeccionarlas
vi.mock("react-apexcharts", async () => {
  const React = await import("react");
  return { default: (props: { type?: string; series?: unknown; options?: unknown }) => React.createElement("div", { "data-testid": "apexchart", "data-tipo": props.type, "data-series": JSON.stringify(props.series ?? []) }) };
});
