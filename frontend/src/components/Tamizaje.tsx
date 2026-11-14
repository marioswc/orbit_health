import { FormEvent, memo, useState } from "react";
import { post } from "../api/client";
import type { RespuestaTamizaje } from "../api/tipos";

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
    <section className="panel">
      <h2>Tamizaje de ánimo (PHQ-2)</h2>
      <p className="suave">Últimas dos semanas. Resultado privado: no se transmite. Es un tamizaje, no un diagnóstico.</p>
      <form onSubmit={enviar}>
        {PREGUNTAS.map((p, i) => (
          <div key={p} className="fila">
            <span style={{ flex: "1 1 100%" }}>{p}</span>
            <select value={resp[i] ?? ""} onChange={(e) => setResp(resp.map((r, j) => (j === i ? Number(e.target.value) : r)))}>
              <option value="">Selecciona…</option>
              {OPCIONES.map((o, v) => <option key={o} value={v}>{o}</option>)}
            </select>
          </div>
        ))}
        <button type="submit">Ver resultado</button>
      </form>
      {error && <p className="error">{error}</p>}
      {res && (
        <div>
          <p>Puntaje {res.total}/6 · {res.positivo ? "positivo en tamizaje" : "negativo"}</p>
          {res.capsulas.map((c) => <div key={c.id} className="item"><strong>{c.titulo}</strong><br />{c.contenido_markdown}</div>)}
        </div>
      )}
    </section>
  );
}

export default memo(Tamizaje);
