import { FormEvent, memo, useCallback, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import type { NotaDiario } from "../types/bienestar";

function DiarioTripulante({ tripulanteId }: { tripulanteId: string }) {
  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [notas, setNotas] = useState<NotaDiario[] | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);

  const cargar = useCallback(
    () => api<NotaDiario[]>(`/diario/${tripulanteId}`).then(setNotas).catch(() => setNotas([])),
    [tripulanteId],
  );
  useEffect(() => { setNotas(null); cargar(); }, [cargar]);

  async function guardar(e: FormEvent) {
    e.preventDefault();
    if (!contenido.trim()) return setMsg({ ok: false, texto: "Escribe algo antes de guardar" });
    try {
      await post("/diario", { tripulante_id: tripulanteId, titulo: titulo || null, contenido });
      setContenido(""); setTitulo("");
      setMsg({ ok: true, texto: "Guardado. La nota permanece en este equipo y no se envía a ningún lado." });
      cargar();
    } catch (err) { setMsg({ ok: false, texto: (err as Error).message }); }
  }

  return (
    <section className="tarjeta pieza">
      <h2>Diario personal</h2>
      <p className="suave">Almacenamiento local seguro, desconectado de la telemetría externa.</p>
      <form onSubmit={guardar} className="formulario">
        <div className="campo">
          <label className="campo-etiqueta" htmlFor="diario-titulo">Título <span className="opcional">opcional</span></label>
          <input id="diario-titulo" value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Ej. Un buen día de ejercicio" maxLength={120} />
        </div>
        <div className="campo">
          <label className="campo-etiqueta" htmlFor="diario-texto">Nota</label>
          <textarea id="diario-texto" value={contenido} onChange={(e) => setContenido(e.target.value)} placeholder="Escribe aquí…" />
        </div>
        <div className="fila-acciones">
          <button type="submit" className="btn-primario">Guardar nota</button>
        </div>
        {msg && <Alerta tono={msg.ok ? "ok" : "error"}>{msg.texto}</Alerta>}
      </form>

      <h3 className="subtitulo">Notas anteriores</h3>
      {notas === null ? (
        <span className="esqueleto" style={{ height: 64 }} aria-busy="true" />
      ) : notas.length === 0 ? (
        <p className="vacio">Aún no hay notas. La primera que guardes aparecerá aquí.</p>
      ) : (
        <ol className="linea-tiempo">
          {notas.map((n) => (
            <li key={n.id}>
              <time className="fecha-mono" dateTime={n.ts}>{n.ts.slice(0, 16).replace("T", " ")}</time>
              <strong>{n.titulo ?? "Nota"}</strong>
              <p>{n.contenido}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export default memo(DiarioTripulante);
