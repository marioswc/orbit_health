import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useZonaSeleccionada } from "../hooks/useZonaSeleccionada";

afterEach(() => window.history.replaceState({}, "", "/"));

describe("useZonaSeleccionada", () => {
  it("arranca con el cuerpo completo y la capa traje", () => {
    const { result } = renderHook(() => useZonaSeleccionada());
    expect(result.current).toMatchObject({ zona: "cardio", acercado: false, capa: "traje" });
  });
  it("elegir acerca la camara y revela la capa inicial de la zona", () => {
    const { result } = renderHook(() => useZonaSeleccionada());
    act(() => result.current.elegir("brazos"));
    expect(result.current).toMatchObject({ zona: "brazos", acercado: true });
    expect(result.current.capa).not.toBe("traje");
  });
  it("elegir la misma zona otra vez aleja; alejar vuelve al traje", () => {
    const { result } = renderHook(() => useZonaSeleccionada());
    act(() => result.current.elegir("snc"));
    act(() => result.current.elegir("snc"));
    expect(result.current).toMatchObject({ acercado: false, capa: "traje" });
    act(() => result.current.elegir("resp"));
    act(() => result.current.alejar());
    expect(result.current).toMatchObject({ zona: "resp", acercado: false, capa: "traje" });
  });
  it("ignora zonas inexistentes", () => {
    const { result } = renderHook(() => useZonaSeleccionada());
    act(() => result.current.elegir("no-existe"));
    expect(result.current.zona).toBe("cardio");
  });
  it("lee ?zona= y ?capa= de la URL", () => {
    window.history.replaceState({}, "", "/?zona=piernas&capa=hueso");
    const { result } = renderHook(() => useZonaSeleccionada());
    expect(result.current).toMatchObject({ zona: "piernas", acercado: true, capa: "hueso" });
  });
  it("valores invalidos en la URL se ignoran", () => {
    window.history.replaceState({}, "", "/?zona=xx&capa=yy");
    const { result } = renderHook(() => useZonaSeleccionada());
    expect(result.current).toMatchObject({ zona: "cardio", acercado: false, capa: "traje" });
  });
});
