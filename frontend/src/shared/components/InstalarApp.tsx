import { useEffect, useState, useSyncExternalStore } from "react";
import { useTranslation } from "../../i18n";
import { actualizacionLista, aplicarActualizacion, instalar, puedeInstalar, suscribir, yaInstalada } from "../pwa";

/** Avisos de la app instalable: botón "Instalar ORBIT" (cuando el navegador lo permite) y "Hay una versión nueva". */
export default function InstalarApp() {
  const { t } = useTranslation("bienvenida");
  useSyncExternalStore(suscribir, () => `${puedeInstalar()}|${actualizacionLista()}`);
  const [oculto, setOculto] = useState(false);
  useEffect(() => { if (yaInstalada()) setOculto(true); }, []);

  if (actualizacionLista()) {
    return (
      <div className="instalar-app" role="status">
        <span>{t("actualizar.texto")}</span>
        <button type="button" className="boton" onClick={aplicarActualizacion}>{t("actualizar.boton")}</button>
      </div>
    );
  }
  if (puedeInstalar() && !oculto) {
    return (
      <div className="instalar-app" role="status">
        <span>{t("instalar.texto")}</span>
        <button type="button" className="boton" onClick={() => void instalar()}>{t("instalar.boton")}</button>
        <button type="button" className="boton" aria-label={t("instalar.luego")} onClick={() => setOculto(true)}>×</button>
      </div>
    );
  }
  return null;
}
