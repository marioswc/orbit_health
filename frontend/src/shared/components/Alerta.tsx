import type { ReactNode } from "react";

export type TonoAlerta = "info" | "aviso" | "error" | "ok";

interface Props {
  tono?: TonoAlerta;
  titulo?: string;
  children?: ReactNode;
  /** Acción a la derecha (botón o enlace). */
  accion?: ReactNode;
}

const P = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;
const ICONOS: Record<TonoAlerta, ReactNode> = {
  info: <svg {...P}><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.8v.1" /></svg>,
  aviso: <svg {...P}><path d="M12 4 3 19.5h18L12 4z" /><path d="M12 10v4.5M12 17.2v.1" /></svg>,
  error: <svg {...P}><circle cx="12" cy="12" r="9" /><path d="m9 9 6 6M15 9l-6 6" /></svg>,
  ok: <svg {...P}><circle cx="12" cy="12" r="9" /><path d="m8.2 12.3 2.6 2.6 5-5.4" /></svg>,
};

/** Alerta de aplicación: icono en baldosa, título opcional y cuerpo. `error` usa role="alert"; el resto, "status". */
export default function Alerta({ tono = "info", titulo, children, accion }: Props) {
  return (
    <div className={`alerta ${tono}`} role={tono === "error" ? "alert" : "status"}>
      <span className="alerta-icono">{ICONOS[tono]}</span>
      <div className="alerta-texto">
        {titulo && <strong>{titulo}</strong>}
        {children && <p>{children}</p>}
      </div>
      {accion && <div className="alerta-accion">{accion}</div>}
    </div>
  );
}
