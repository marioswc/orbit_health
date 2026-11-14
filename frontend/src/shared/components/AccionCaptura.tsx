import { useTranslation } from "../../i18n";
import { useCaptura } from "../capturaContext";

/** Boton "Captura manual" del encabezado de pagina (escritorio). En pantallas angostas lo reemplaza el boton flotante de App. */
export default function AccionCaptura() {
  const c = useCaptura();
  const { t } = useTranslation();
  if (!c) return null;
  return (
    <button type="button" className="btn-primario accion-captura" onClick={c.alAbrir} disabled={!c.disponible}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
      {t("capture.button")}
    </button>
  );
}
