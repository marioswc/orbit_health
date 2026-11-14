import { useCallback, useState } from "react";
import Alerta from "../../../shared/components/Alerta";
import Drawer from "../../../shared/components/Drawer";
import { useExplicaciones } from "../hooks/useExplicaciones";
import { nombreIndicador } from "../utils/nombreIndicador";

const SECCIONES = [
  ["que_es", "Qué es"], ["por_que_se_mide", "Por qué se mide"], ["como_medirlo", "Cómo medirlo"],
  ["en_el_espacio", "Qué cambia en el espacio"], ["cuando_avisar", "Cuándo avisar"],
] as const;

/** Boton "?" junto a un indicador: abre un modal con la explicacion del servidor. */
export default function ExplicacionIndicador({ clave }: { clave: string }) {
  const [abierto, setAbierto] = useState(false);
  const { datos, error } = useExplicaciones(abierto);
  const cerrar = useCallback(() => setAbierto(false), []);
  const e = datos?.explicaciones[clave];
  const nombre = nombreIndicador(clave);
  return (
    <>
      <button type="button" className="ghost ayuda-ind" aria-label={`Qué es ${nombre}`} onClick={() => setAbierto(true)}>?</button>
      <Drawer abierto={abierto} alCerrar={cerrar} titulo={nombre}>
        {error && <Alerta tono="error">{error}</Alerta>}
        {!datos && !error && <span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}
        {datos && !e && <p className="suave">Este indicador aún no tiene explicación.</p>}
        {datos && e && (
          <div className="explicacion">
            {SECCIONES.map(([k, t]) => <section key={k}><h3>{t}</h3><p>{e[k]}</p></section>)}
            <p className="fuente">{datos.aviso} Estado: {datos.estado}.</p>
            <ul className="fuentes">{e.fuentes.map((u) => <li key={u}><a className="enlace" href={u} target="_blank" rel="noopener noreferrer">{u.replace("https://www.nasa.gov/", "nasa.gov/")}</a></li>)}</ul>
          </div>
        )}
      </Drawer>
    </>
  );
}
