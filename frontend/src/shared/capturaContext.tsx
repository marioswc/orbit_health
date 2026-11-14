import { createContext, useContext } from "react";

export interface AccionCapturaValor { alAbrir: () => void; disponible: boolean }

/** Permite que el encabezado de cada pagina muestre "Captura manual" sin que shared dependa de app/. Lo provee App. */
export const CapturaContext = createContext<AccionCapturaValor | null>(null);
export const useCaptura = () => useContext(CapturaContext);
