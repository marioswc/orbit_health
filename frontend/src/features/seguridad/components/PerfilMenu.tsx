import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "../../../i18n";

interface Props { nombre: string; rol: string; id: string; alSalir: () => void }

const iniciales = (nombre: string) =>
  nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("") || "?";

/** Circulo con las iniciales del tripulante en sesion; al abrirlo muestra su perfil y la salida. */
export default function PerfilMenu({ nombre, rol, id, alSalir }: Props) {
  const { t } = useTranslation();
  const [abierto, setAbierto] = useState(false);
  const raiz = useRef<HTMLDivElement>(null);
  const panelId = useId();

  useEffect(() => {
    if (!abierto) return;
    const fuera = (e: MouseEvent) => { if (!raiz.current?.contains(e.target as Node)) setAbierto(false); };
    const tecla = (e: KeyboardEvent) => { if (e.key === "Escape") setAbierto(false); };
    document.addEventListener("mousedown", fuera);
    document.addEventListener("keydown", tecla);
    return () => { document.removeEventListener("mousedown", fuera); document.removeEventListener("keydown", tecla); };
  }, [abierto]);

  return (
    <div className="perfil" ref={raiz}>
      <button type="button" className="perfil-avatar" aria-expanded={abierto} aria-controls={panelId} aria-haspopup="true"
        aria-label={t("topbar.profileAria", { nombre })} onClick={() => setAbierto((v) => !v)}>
        {iniciales(nombre)}
      </button>
      {abierto && (
        <div className="perfil-panel" id={panelId} role="group" aria-label={t("topbar.profile")}>
          <div className="perfil-datos">
            <span className="perfil-avatar grande" aria-hidden="true">{iniciales(nombre)}</span>
            <div>
              <strong>{nombre}</strong>
              <span>{rol}</span>
              <span className="perfil-id">{id}</span>
            </div>
          </div>
          <button type="button" className="perfil-salir" onClick={alSalir}>{t("topbar.logout")}</button>
        </div>
      )}
    </div>
  );
}
