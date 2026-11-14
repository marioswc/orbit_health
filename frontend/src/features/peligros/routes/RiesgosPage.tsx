import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import { nombreIndicador } from "../../monitor/utils/nombreIndicador";
import type { Cobertura, MarcoPeligros } from "../types/peligros";

const COBERTURA: Record<Cobertura, string> = { cubierto: "Cubierto", parcial: "Parcial", no_cubierto: "No cubierto" };

/** Marco de peligros y riesgos del HRP de la NASA y lo que ORBIT Health cubre de verdad (sin prometer de mas). */
export default function RiesgosPage() {
  const [marco, setMarco] = useState<MarcoPeligros | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api<MarcoPeligros>("/peligros").then(setMarco).catch((e) => setError(e.message)); }, []);

  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta="Riesgos" titulo="Peligros del vuelo espacial" descripcion="El marco de peligros y riesgos del Programa de Investigación Humana de la NASA, y qué parte vigila este prototipo.">
        {marco && (
          <span className="chip-estado" aria-label="Cobertura de riesgos">
            {marco.resumen_cobertura.cubierto} cubiertos · {marco.resumen_cobertura.parcial} parciales · {marco.resumen_cobertura.no_cubierto} sin cubrir de {marco.resumen_cobertura.total}
          </span>
        )}
      </EncabezadoPagina>
      {error && <Alerta tono="error" titulo="No se pudo cargar el marco de riesgos">{error}</Alerta>}
      {!marco && !error && <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      {marco && (
        <>
          <section className="peligros-rejilla" aria-label="Los cinco peligros">
            {Object.entries(marco.peligros).map(([id, p]) => (
              <article key={id} className="tarjeta pieza peligro">
                <h2>{p.nombre}</h2>
                <p className="suave">{p.resumen}</p>
                <p className="peligro-orbit"><strong>Cómo responde ORBIT</strong>{p.como_responde_orbit}</p>
                <a className="enlace" href={p.url} target="_blank" rel="noopener noreferrer">{p.nombre_oficial} (NASA)</a>
              </article>
            ))}
          </section>
          <section className="tarjeta pieza" aria-label="Riesgos y cobertura">
            <h2>Riesgos del HRP</h2>
            <p className="suave">La asociación entre indicadores y peligros es una decisión de diseño del equipo; la NASA no los clasifica así.</p>
            <ul className="riesgos">
              {marco.riesgos.map((r) => (
                <li key={r.nombre_oficial}>
                  <span className={`cobertura ${r.cobertura}`}>{COBERTURA[r.cobertura]}</span>
                  <a className="enlace" href={r.url} target="_blank" rel="noopener noreferrer">{r.nombre_oficial.replace(/^Risk of /, "")}</a>
                  {r.indicadores.length > 0 && <span className="riesgo-ind">{r.indicadores.map(nombreIndicador).join(" · ")}</span>}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
