import { FormEvent, memo, useState } from "react";
import { post } from "../../../shared/api/client";
import Selector from "../../../shared/components/Selector";
import type { RespuestaTamizaje } from "../types/bienestar";

const OPCIONES = ["Nunca", "Varios días", "Más de la mitad de los días", "Casi todos los días"];
const PREGUNTAS = [
  "Poco interés o placer en hacer las cosas",
  "Sentirse desanimado, deprimido o sin esperanza",
];

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
    <section className="tarjeta">
      <h2>Tamizaje de ánimo (PHQ-2)</h2>
      <p className="suave">Últimas dos semanas. Resultado privado: no se transmite. Es un tamizaje, no un diagnóstico.</p>
      <form onSubmit={enviar}>
        {PREGUNTAS.map((p, i) => (
          <div key={p} className="pregunta">
            <span id={`preg-${i}`}>{p}</span>
            <Selector
              etiqueta={p} valor={resp[i] === null ? "" : String(resp[i])}
              alCambiar={(v) => setResp(resp.map((r, j) => (j === i ? Number(v) : r)))}
              opciones={OPCIONES.map((o, v) => ({ valor: String(v), etiqueta: o }))}
            />
          </div>
        ))}
        <button type="submit">Ver resultado</button>
      </form>
      {error && <p className="error" role="alert" style={{ marginTop: 16 }}>{error}</p>}
      {res && (
        <div style={{ marginTop: 16 }}>
          <p>Puntaje {res.total}/6 · {res.positivo ? "positivo en tamizaje" : "negativo"}</p>
          {res.capsulas.map((c) => <div key={c.id} className="item"><strong>{c.titulo}</strong><span>{c.contenido_markdown}</span></div>)}
        </div>
      )}
    </section>
  );
}

export default memo(Tamizaje);
