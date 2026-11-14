import type { Tripulante } from "../types/tripulante";

interface Props { tripulantes: Tripulante[]; valor: string; alCambiar: (id: string) => void }

export default function SelectorTripulante({ tripulantes, valor, alCambiar }: Props) {
  return (
    <select value={valor} onChange={(e) => alCambiar(e.target.value)} aria-label="Tripulante">
      {tripulantes.map((t) => <option key={t.id} value={t.id}>{t.nombre} · {t.rol}</option>)}
    </select>
  );
}
