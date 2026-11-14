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
            {e.senales_a_vigilar && e.senales_a_vigilar.length > 0 && (
              <section>
                <h3>Señales a vigilar (NASA)</h3>
                <ul className="citas-nasa">
                  {e.senales_a_vigilar.map((s) => (
                    <li key={s.cita}>
                      <p>{s.texto}</p>
                      <blockquote className="cita-textual">“{s.cita}”</blockquote>
                      <a className="enlace" href={s.fuente} target="_blank" rel="noopener noreferrer">{s.fuente.replace("https://www.nasa.gov/", "nasa.gov/")}</a>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {e.medidas_nasa && e.medidas_nasa.length > 0 && (
              <section>
                <h3>Medidas con fuente NASA</h3>
                <ul className="citas-nasa">
                  {e.medidas_nasa.map((m) => (
                    <li key={m.cita}>
                      <p>{m.texto}</p>
                      <blockquote className="cita-textual">“{m.cita}”</blockquote>
                      <a className="enlace" href={m.fuente} target="_blank" rel="noopener noreferrer">{m.fuente.replace("https://www.nasa.gov/", "nasa.gov/")}</a>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {e.nota_nasa && (
              <section>
                <h3>Guía de la NASA</h3>
                <p className="suave">{e.nota_nasa}</p>
              </section>
            )}
            {e.habitos_generales && e.habitos_generales.length > 0 && (
              <section>
                <h3>Hábitos generales (equipo)</h3>
                <ul>{e.habitos_generales.map((h) => <li key={h}>{h}</li>)}</ul>
                {e.habitos_generales_origen && <p className="fuente">{e.habitos_generales_origen}</p>}
              </section>
            )}
            <p className="fuente">{datos.aviso} {t("expl.estado", { estado: datos.estado })}</p>
            <ul className="fuentes">{e.fuentes.map((u) => <li key={u}><a className="enlace" href={u} target="_blank" rel="noopener noreferrer">{u.replace("https://www.nasa.gov/", "nasa.gov/")}</a></li>)}</ul>
          </div>
        )}
      </Drawer>
    </>
  );
}
