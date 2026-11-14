import { FormEvent, memo, useCallback, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import type { RespuestaAnimo, SerieAnimo } from "../types/bienestar";

const ESCALA = [
  { valor: 1, etiqueta: "1 · Muy bajo" },
  { valor: 2, etiqueta: "2 · Bajo" },
  { valor: 3, etiqueta: "3 · Estable" },
  { valor: 4, etiqueta: "4 · Bien" },
  { valor: 5, etiqueta: "5 · Muy bien" },
] as const;

/** Registro diario de animo (1-5). Privado y exclusivo del tripulante; nunca se transmite. */
function AnimoDiario({ tripulanteId }: { tripulanteId: string }) {
  const [valor, setValor] = useState<number | null>(null);
  const [serie, setSerie] = useState<SerieAnimo | null>(null);
  const [res, setRes] = useState<RespuestaAnimo | null>(null);
  const [error, setError] = useState("");

  const cargar = useCallback(
    () => api<SerieAnimo>(`/animo/${tripulanteId}`).then(setSerie).catch(() => setSerie(null)),
    [tripulanteId],
  );
  useEffect(() => { cargar(); setRes(null); setValor(null); }, [cargar]);

  async function guardar(e: FormEvent) {
    e.preventDefault();
    if (valor === null) return setError("Elige un nivel del 1 al 5");
    setError("");
    try {
      const r = await post<RespuestaAnimo>("/animo", { tripulante_id: tripulanteId, valor });
      setRes(r);
      cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="tarjeta">
      <h2>Ánimo diario</h2>
      <p className="suave">Escala personal 1–5. Privado: nunca entra a la cola de salida.</p>

      <form onSubmit={guardar}>
        <div className="animo-escala" role="group" aria-label="Nivel de ánimo de 1 a 5">
          {ESCALA.map((op) => (
            <button
              key={op.valor}
              type="button"
              className={valor === op.valor ? "activo" : ""}
              aria-pressed={valor === op.valor}
              onClick={() => setValor(op.valor)}
            >
              {op.etiqueta}
            </button>
          ))}
        </div>
        <div className="fila" style={{ marginTop: 12 }}>
          <button type="submit">Registrar ánimo</button>
          {serie?.media !== null && serie?.media !== undefined && (
            <span className="suave">Media 14 días: <strong>{serie.media}</strong> ({serie.puntos.length} {serie.puntos.length === 1 ? "registro" : "registros"})</span>
          )}
        </div>
      </form>

      {error && <Alerta tono="error" titulo="No se pudo registrar">{error}</Alerta>}

      {res && (
        <div className="animo-res">
          <Alerta tono={res.bajo || res.aviso_linea_base ? "aviso" : "ok"} titulo={`Registrado: ${res.valor}/5`}>
            {res.bajo ? "Ánimo bajo detectado." : res.aviso_linea_base ? "Desvío respecto a tu línea base." : "Dentro de tu rango habitual."}
          </Alerta>
          {res.capsulas.map((c) => (
            <div key={c.id} className="item"><strong>{c.titulo}</strong><br />{c.contenido_markdown}</div>
          ))}
        </div>
      )}
    </section>
  );
}

export default memo(AnimoDiario);

