import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import CambioIdioma from "../../shared/components/CambioIdioma";
import ToggleIdioma from "../../shared/components/ToggleIdioma";
import { cargarIdioma, changeLanguage, getCurrentLanguage, normalizeLanguage, translate, useTranslation } from "..";

beforeAll(async () => { await cargarIdioma("en"); });
afterEach(async () => { await changeLanguage("es"); localStorage.clear(); });

describe("translate", () => {
  it("traduce en espanol e ingles", () => {
    expect(translate("es", "common", "nav.historial")).toBe("Historial");
    expect(translate("en", "common", "nav.historial")).toBe("History");
  });
  it("interpola variables y acepta ns:clave", () => {
    expect(translate("en", "common", "prototype.text", { version: "0.1.0", estado: "x" })).toBe("Thresholds v0.1.0: x.");
    expect(translate("es", "common", "sistema:audit.intact", { total: 8 })).toBe("Cadena íntegra (8 eventos)");
  });
  it("usa plurales segun count", () => {
    expect(translate("es", "historial", "count", { count: 1 })).toBe("1 indicador");
    expect(translate("es", "historial", "count", { count: 3 })).toBe("3 indicadores");
    expect(translate("en", "historial", "count", { count: 1 })).toBe("1 indicator");
    expect(translate("en", "historial", "count", { count: 3 })).toBe("3 indicators");
  });
  it("si falta la clave devuelve la clave; si falta en EN cae al espanol", () => {
    expect(translate("en", "common", "no.existe")).toBe("no.existe");
  });
});

describe("normalizeLanguage", () => {
  it("reconoce es-MX y en-US", () => {
    expect(normalizeLanguage("es-MX")).toBe("es");
    expect(normalizeLanguage("EN-us")).toBe("en");
    expect(normalizeLanguage("fr")).toBeNull();
  });
});

describe("cambio de idioma", () => {
  it("persiste, actualiza <html lang> y re-renderiza", async () => {
    const { result } = renderHook(() => useTranslation());
    expect(result.current.t("nav.monitor")).toBe("Monitor");
    await act(async () => { await changeLanguage("en"); });
    expect(getCurrentLanguage()).toBe("en");
    expect(localStorage.getItem("i18nextLng")).toBe("en");
    expect(document.documentElement.lang).toBe("en");
    expect(result.current.t("nav.historial")).toBe("History");
    expect(result.current.locale).toBe("en-US");
  });

  it("el conmutador ES | EN muestra el modal de cambio y luego aplica el idioma", async () => {
    render(<><ToggleIdioma /><CambioIdioma /></>);
    expect(screen.getByRole("button", { name: "ES" })).toHaveAttribute("aria-pressed", "true");
    await act(async () => { screen.getByRole("button", { name: "EN" }).click(); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Switching to English"));
    await waitFor(() => expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "true"));
    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("status")).toBeNull(), { timeout: 2500 }); // el modal se retira solo
  });
});
