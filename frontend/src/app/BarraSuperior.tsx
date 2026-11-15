import type { ReactNode } from "react";
import ToggleIdioma from "../shared/components/ToggleIdioma";
import ToggleTema from "../shared/components/ToggleTema";
import type { Tema } from "../shared/hooks/useTema";

interface Props {
  /** Nombre de la vista actual (migas de pan simples). */
  titulo?: string;
  tema: Tema;
  alAlternarTema: () => void;
  /** Selector de tripulante (lo compone App para no acoplar esta barra a una feature). */
  selector?: ReactNode;
  /** Perfil de la sesion: siempre el ultimo elemento de la barra. */
  perfil?: ReactNode;
}

/** Cabecera delgada: vista actual a la izquierda; tripulante y tema a la derecha. Las vistas viven en el menu lateral. */
export default function BarraSuperior({ titulo, tema, alAlternarTema, selector, perfil }: Props) {
  return (
    <header className="barra">
      <span className="barra-titulo">{titulo}</span>
      <div className="barra-acciones">
        {selector}
        <ToggleIdioma />
        <ToggleTema tema={tema} alternar={alAlternarTema} />
        {perfil}
      </div>
    </header>
  );
}
