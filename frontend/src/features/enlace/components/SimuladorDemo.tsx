import { memo, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { ComparativaOrbit, EscenarioDemo } from "../types/cola";

const PERFILES = [
  { valor: "luna", etiqueta: "Luna" },
  { valor: "marte_cercano", etiqueta: "Marte mín" },
  { valor: "marte_medio", etiqueta: "Marte medio" },
  { valor: "marte", etiqueta: "Marte máx" },
];

function formatoTiempo(s: number): string {
  if (s === 0) return "0 s";
  if (s < 60) return `${s} s`;
  return `${Math.round((s / 60) * 10) / 10} min`;
}

/** Escenarios guionizados y linea de tiempo comparativa con y sin ORBIT. */
function SimuladorDemo() {
  const [escenarios, setEscenarios] = useState<EscenarioDemo[]>([]);
  const [entorno, setEntorno] = useState("marte");
  const [comp, setComp] = useState<ComparativaOrbit | null>(null);
  const [resultado, setResultado] = useState<{ escenario: string; pasos: { paso: string; nivel?: string; prioridad?: number; despachados?: number }[] } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<EscenarioDemo[]>("/demo/escenarios").then(setEscenarios).catch(() => {});
  }, []);

  useEffect(() => {
    api<ComparativaOrbit>(`/demo/comparativa?entorno=${encodeURIComponent(entorno)}`)
      .then((d) => { setComp(d); setError(""); })
      .catch((e) => setError((e as Error).message));
  }, [entorno]);

  async function correr(id: string, reconectar: boolean) {
    setError("");
    try {
      const r = await post<NonNullable<typeof resultado>>(`/demo/escenarios/${encodeURIComponent(id)}?reconectar=${reconectar}`, {});
      setResultado(r);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="demo-bloque">
      {comp && (
        <section className="tarjeta pieza comparativa" aria-label="Comparativa con y sin ORBIT">
          <div className="comparativa-cab">
            <div>
              <h2>El dilema de la latencia: {comp.evento}</h2>
              <p className="suave">
                Ventana sin respuesta de Tierra: <strong>{comp.ventana_sin_apoyo_min} min</strong> ({comp.ventana_sin_apoyo_s} s).
              </p>
            </div>
            <Segmentado etiqueta="Entorno comparativa" opciones={PERFILES} valor={entorno} alCambiar={setEntorno} />
          </div>

          <div className="comparativa-cols">
            <div className="comparativa-col con">
              <h3>Con ORBIT a bordo</h3>
              <ol>
                {comp.con_orbit.map((p, i) => (
                  <li key={i}>
                    <span className="t-mono">{formatoTiempo(p.t_s)}</span>
                    <span>{p.texto}</span>
                  </li>
                ))}
              </ol>
            </div>
            <div className="comparativa-col sin">
              <h3>Sin ORBIT</h3>
              <ol>
                {comp.sin_orbit.map((p, i) => (
                  <li key={i}>
                    <span className="t-mono">{formatoTiempo(p.t_s)}</span>
                    <span>{p.texto}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <p className="fuente">{comp.aviso}</p>
        </section>
      )}

      {escenarios.length > 0 && (
        <section className="tarjeta pieza escenarios" aria-label="Escenarios reproducibles de demo">
          <h2>Escenarios de demostración</h2>
          <p className="suave">Simulan casos completos en la base local para ensayar la cola y las alertas.</p>
          <div className="escenarios-lista">
            {escenarios.map((e) => (
              <div key={e.id} className="escenario-item">
                <div>
                  <strong>{e.id.replace(/_/g, " ")}</strong>
                  <p className="suave">{e.descripcion}</p>
                </div>
                <div className="fila">
                  <button type="button" onClick={() => correr(e.id, false)}>Ejecutar</button>
                  <button type="button" className="ghost" onClick={() => correr(e.id, true)}>Ejecutar + reconectar</button>
                </div>
              </div>
            ))}
          </div>

          {resultado && (
            <div className="escenario-res">
              <strong>Último escenario ejecutado: {resultado.escenario}</strong>
              <ul>
                {resultado.pasos.map((p, idx) => (
                  <li key={idx}>
                    <span>{p.paso}</span>
                    {p.nivel && <span className={`badge ${p.nivel}`}>{p.nivel}</span>}
                    {p.despachados !== undefined && <span className="suave">{p.despachados} despachados</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {error && <Alerta tono="error" titulo="No se pudo cargar el simulador">{error}</Alerta>}
    </div>
  );
}

export default memo(SimuladorDemo);

