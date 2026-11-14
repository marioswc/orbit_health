import { useTranslation } from "../../../i18n";
import Selector from "../../../shared/components/Selector";
import type { Tripulante } from "../types/tripulante";

interface Props { tripulantes: Tripulante[]; valor: string; alCambiar: (id: string) => void }

export default function SelectorTripulante({ tripulantes, valor, alCambiar }: Props) {
  const { t } = useTranslation("shared");
  return (
    <Selector
      etiqueta={t("crew")} valor={valor} alCambiar={alCambiar} marcador={t("crew")}
      opciones={tripulantes.map((x) => ({ valor: x.id, etiqueta: `${x.nombre} · ${x.rol}` }))}
    />
  );
}
