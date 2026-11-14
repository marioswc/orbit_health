import { FormEvent, memo, useCallback, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import type { NotaDiario } from "../types/bienestar";

function DiarioTripulante({ tripulanteId }: { tripulanteId: string }) {
  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [notas, setNotas] = useState<NotaDiario[]>([]);
  const [msg, setMsg] = useState("");

  const cargar = useCallback(
    () => api<NotaDiario[]>(`/diario/${tripulanteId}`).then(setNotas).catch(() => setNotas([])),
    [tripulanteId],
  );
  useEffect(() => { cargar(); }, [cargar]);

  async function guardar(e: FormEvent) {
    e.preventDefault();
    if (!contenido.trim()) return;
    try {
      await post("/diario", { tripulante_id: tripulanteId, titulo: titulo || null, contenido });
      setContenido(""); setTitulo("");
      setMsg("Guardado. La nota permanece en este equipo y no se envía a ningún lado.");
      cargar();
    } catch (err) { setMsg((err as Error).message); }
  }

  return (
    <section className="tarjeta">
      <h2>Diario personal</h2>
      <div className="etiqueta-local">Almacenamiento local seguro: desconectado de la telemetría externa</div>
      <form onSubmit={guardar}>
        <div className="fila"><input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título (opcional)" /></div>
        <textarea value={contenido} onChange={(e) => setContenido(e.target.value)} placeholder="Escribe aquí…" />
        <div className="fila"><button type="submit" className="btn-primario">Guardar nota</button></div>
      </form>
      {msg && <p className="suave">{msg}</p>}
      {notas.map((n) => (
        <div key={n.id} className="item"><strong>{n.titulo ?? "Nota"}</strong> · <span className="suave">{n.ts.slice(0, 16).replace("T", " ")}</span><br />{n.contenido}</div>
      ))}
    </section>
  );
}

export default memo(DiarioTripulante);
