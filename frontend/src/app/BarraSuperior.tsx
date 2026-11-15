import type { ReactNode } from "react";
import { useTranslation } from "../i18n";
import ToggleIdioma from "../shared/components/ToggleIdioma";
import ToggleTema from "../shared/components/ToggleTema";
import type { Tema } from "../shared/hooks/useTema";

interface Props {
  tema: Tema;
  alAlternarTema: () => void;
  /** Selector de tripulante (lo compone App para no acoplar esta barra a una feature). */
  selector?: ReactNode;
  /** Perfil de la sesion: siempre el ultimo elemento de la barra. */
  perfil?: ReactNode;
}

/** Cabecera delgada: vista actual a la izquierda; tripulante y tema a la derecha. Las vistas viven en el menu lateral. */
export default function BarraSuperior({ tema, alAlternarTema, selector, perfil }: Props) {
  const { t } = useTranslation("bienvenida");
  return (
    <header className="barra">
      <div className="barra-acciones">
        {selector}
        <ToggleIdioma />
        <ToggleTema tema={tema} alternar={alAlternarTema} />
        <button
          type="button"
          className="icono"
          aria-label={t("ayuda")}
          title={t("ayuda")}
          onClick={() => window.dispatchEvent(new Event("orbit:abrir-bienvenida"))}
        >
          ?
        </button>
        {perfil}
      </div>
    </header>
  );
}
