import { useCallback, useState } from "react";
import { CAPAS, ZONAS, type Capa } from "../zonas";

/** Estado inicial opcional desde la URL (?zona=brazos&capa=musculo&zoom=0 para ver el cuerpo completo): sirve para compartir o ensayar una vista de la demo. */
function desdeUrl() {
  const q = new URLSearchParams(window.location.search);
  const zona = ZONAS.find((z) => z.id === q.get("zona"));
  const capa = CAPAS.find((c) => c.id === q.get("capa"));
  return { zona: zona?.id, capa: capa?.id, acercado: !!zona && q.get("zoom") !== "0" };
}

/**
 * Zona elegida, camara acercada y capa visible (traje / musculo / hueso / organos).
 * Elegir una zona acerca la camara y revela su capa; elegir otra vez la misma alterna el acercamiento.
 */
export function useZonaSeleccionada(inicial = "cardio") {
  const [ini] = useState(desdeUrl);
  const [zona, setZona] = useState(ini.zona ?? inicial);
  const [acercado, setAcercado] = useState(ini.acercado);
  const [capa, setCapa] = useState<Capa>(ini.capa ?? (ini.zona ? ZONAS.find((z) => z.id === ini.zona)!.capaInicial : "traje"));

  const elegir = useCallback((id: string) => {
    const z = ZONAS.find((x) => x.id === id);
    if (!z) return;
    if (id === zona && acercado) { setAcercado(false); setCapa("traje"); return; }
    setZona(id); setAcercado(true); setCapa(z.capaInicial);
  }, [zona, acercado]);

  const alejar = useCallback(() => { setAcercado(false); setCapa("traje"); }, []);
  return { zona, acercado, capa, setCapa, elegir, alejar };
}
