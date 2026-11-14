import type { ReactNode } from "react";

interface Props {
  /** Rotulo corto en mayuscula sobre el titulo. */
  etiqueta: string;
  titulo: string;
  descripcion: string;
  /** Contenido a la derecha (estado, chips). */
  children?: ReactNode;
}

/** Encabezado comun de las vistas secundarias. */
export default function EncabezadoPagina({ etiqueta, titulo, descripcion, children }: Props) {
  return (
    <header className="encabezado">
      <div>
        <span className="kicker">{etiqueta}</span>
        <h1>{titulo}</h1>
        <p className="cuerpo">{descripcion}</p>
      </div>
      {children && <div className="encabezado-lado">{children}</div>}
    </header>
  );
}
