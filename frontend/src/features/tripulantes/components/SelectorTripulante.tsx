import Selector from "../../../shared/components/Selector";
import type { Tripulante } from "../types/tripulante";

interface Props { tripulantes: Tripulante[]; valor: string; alCambiar: (id: string) => void }

export default function SelectorTripulante({ tripulantes, valor, alCambiar }: Props) {
  return (
    <Selector
      etiqueta="Tripulante" valor={valor} alCambiar={alCambiar} marcador="Tripulante"
      opciones={tripulantes.map((t) => ({ valor: t.id, etiqueta: `${t.nombre} · ${t.rol}` }))}
    />
  );
}
