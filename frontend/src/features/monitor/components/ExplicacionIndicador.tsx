import { useCallback, useState } from "react";
import { useTranslation } from "../../../i18n";
import Alerta from "../../../shared/components/Alerta";
import Drawer from "../../../shared/components/Drawer";
import { useExplicaciones } from "../hooks/useExplicaciones";
import { nombreIndicador } from "../utils/nombreIndicador";

const SECCIONES = ["que_es", "por_que_se_mide", "como_medirlo", "en_el_espacio", "cuando_avisar"] as const;

/** Boton "?" junto a un indicador: abre un modal con la explicacion del servidor. */
export default function ExplicacionIndicador({ clave }: { clave: string }) {
  const { t } = useTranslation("monitor");
  const [abierto, setAbierto] = useState(false);
  const { datos, error } = useExplicaciones(abierto);
  const cerrar = useCallback(() => setAbierto(false), []);
  const e = datos?.explicaciones[clave];
  const nombre = nombreIndicador(clave, t);
  return (
    <>
      <button type="button" className="ghost ayuda-ind" aria-label={t("expl.ariaBoton", { nombre })} onClick={() => setAbierto(true)}>?</button>
      <Drawer abierto={abierto} alCerrar={cerrar} titulo={nombre}>
        {error && <Alerta tono="error">{error}</Alerta>}
        {!datos && !error && <span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}
        {datos && !e && <p className="suave">{t("expl.sinExplicacion")}</p>}
        {datos && e && (
          <div className="explicacion">
            {SECCIONES.map((k) => <section key={k}><h3>{t(`expl.sec.${k}`)}</h3><p>{e[k]}</p></section>)}
            <p className="fuente">{datos.aviso} {t("expl.estado", { estado: datos.estado })}</p>
            <ul className="fuentes">{e.fuentes.map((u) => <li key={u}><a className="enlace" href={u} target="_blank" rel="noopener noreferrer">{u.replace("https://www.nasa.gov/", "nasa.gov/")}</a></li>)}</ul>
          </div>
        )}
      </Drawer>
    </>
  );
}
