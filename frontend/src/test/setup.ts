import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

// jsdom no trae matchMedia ni requestAnimationFrame estable en todos los casos
if (!window.matchMedia) {
  window.matchMedia = ((q: string) => ({ matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false })) as typeof window.matchMedia;
}

// jsdom no implementa scrollIntoView
if (!Element.prototype.scrollIntoView) Element.prototype.scrollIntoView = () => {};
