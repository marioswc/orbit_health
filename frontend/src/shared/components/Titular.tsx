import type { ReactNode } from "react";

/** Titulo de pagina (32px, peso maximo) con una linea de contexto debajo. */
export default function Titular({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div>
      <h1>{titulo}</h1>
      {children && <p className="cuerpo">{children}</p>}
    </div>
  );
}
