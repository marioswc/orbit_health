import { FormEvent, memo, useState } from "react";
import { post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { RespuestaTamizaje } from "../types/bienestar";

const OPCIONES = ["Nunca", "Varios días", "Más de la mitad de los días", "Casi todos los días"];
const PREGUNTAS = [
  "Poco interés o placer en hacer las cosas",
  "Sentirse desanimado, deprimido o sin esperanza",
];
const TOTAL_MAX = 6;

function Tamizaje({ tripulanteId }: { tripulanteId: string }) {
  const [resp, setResp] = useState<(number | null)[]>([null, null]);
  const [res, setRes] = useState<RespuestaTamizaje | null>(null);
  const [error, setError] = useState("");

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (resp.some((r) => r === null)) return setError("Responde las dos preguntas");
    setError("");
    try {
      setRes(await post<RespuestaTamizaje>("/tamizajes", { tripulante_id: tripulanteId, item1: resp[0], item2: resp[1] }));
    } catch (err) { setError((err as Error).message); }
  }

  return (
    <section className="tarjeta pieza">
      <h2>Tamizaje de ánimo (PHQ-2)</h2>
      <p className="suave">Últimas dos semanas. Resultado privado: no se transmite. Es un tamizaje, no un diagnóstico.</p>
      <form onSubmit={enviar} className="formulario">
        {PREGUNTAS.map((p, i) => (
          <fieldset key={p} className="pregunta">
            <legend>{i + 1}. {p}</legend>
            <Segmentado
              rejilla etiqueta={p} valor={resp[i] === null ? "" : String(resp[i])}
              alCambiar={(v) => { setResp(resp.map((r, j) => (j === i ? Number(v) : r))); setError(""); }}
              opciones={OPCIONES.map((o, v) => ({ valor: String(v), etiqueta: o }))}
            />
          </fieldset>
        ))}
        <div className="fila-acciones">
          <button type="submit" className="btn-primario">Ver resultado</button>
        </div>
        {error && <Alerta tono="error">{error}</Alerta>}
      </form>

      {res && (
        <div className="resultado-tamizaje" role="status">
          <div className="medidor" aria-label={`Puntaje ${res.total} de ${TOTAL_MAX}`}>
            {Array.from({ length: TOTAL_MAX }, (_, i) => <span key={i} className={i < res.total ? "lleno" : ""} />)}
          </div>
          <Alerta tono={res.positivo ? "aviso" : "ok"} titulo={`Puntaje ${res.total}/${TOTAL_MAX}`}>
            {res.positivo ? "Positivo en tamizaje. No es un diagnóstico: conviene hablarlo con el médico a bordo." : "Negativo en tamizaje."}
          </Alerta>
          {res.capsulas.map((c) => (
            <article key={c.id} className="capsula">
              <strong>{c.titulo}</strong>
              <p>{c.contenido_markdown}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default memo(Tamizaje);
