import { memo, useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";

interface Prefs { tono: string; detalle: string; recordatorios: string }
const POR_DEFECTO: Prefs = { tono: "directo", detalle: "completo", recordatorios: "normal" };
const TONOS = [{ valor: "directo", etiqueta: "Directo" }, { valor: "calido", etiqueta: "Cálido" }];
const DETALLES = [{ valor: "breve", etiqueta: "Breve" }, { valor: "completo", etiqueta: "Completo" }];
const RECORDATORIOS = [{ valor: "minimo", etiqueta: "Mínimos" }, { valor: "normal", etiqueta: "Normales" }, { valor: "frecuente", etiqueta: "Frecuentes" }];

/** Preferencias del asistente (GET/PUT /api/preferencias/{id}); se guardan al elegir y solo las ve su dueño. */
function AsistentePreferencias({ tripulanteId }: { tripulanteId: string }) {
  const [p, setP] = useState<Prefs>(POR_DEFECTO);
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);
  useEffect(() => { setMsg(null); api<Prefs>(`/preferencias/${tripulanteId}`).then(setP).catch(() => setP(POR_DEFECTO)); }, [tripulanteId]);

  async function cambiar(campo: keyof Prefs, valor: string) {
    const nuevo = { ...p, [campo]: valor };
    setP(nuevo);
    try {
      setP(await api<Prefs>(`/preferencias/${tripulanteId}`, { method: "PUT", body: JSON.stringify(nuevo) }));
      setMsg({ ok: true, texto: "Guardado. Las recomendaciones usarán este estilo." });
    } catch (e) { setMsg({ ok: false, texto: (e as Error).message }); }
  }

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab"><div><h2>Tu asistente</h2><p className="suave">Elige cómo quieres que te hable. Solo se guarda lo que eliges.</p></div></div>
      <div className="formulario">
        <div className="campo"><span className="campo-etiqueta">Tono</span><Segmentado etiqueta="Tono" opciones={TONOS} valor={p.tono} alCambiar={(v) => cambiar("tono", v)} /></div>
        <div className="campo"><span className="campo-etiqueta">Detalle</span><Segmentado etiqueta="Detalle" opciones={DETALLES} valor={p.detalle} alCambiar={(v) => cambiar("detalle", v)} /></div>
        <div className="campo"><span className="campo-etiqueta">Recordatorios</span><Segmentado etiqueta="Recordatorios" opciones={RECORDATORIOS} valor={p.recordatorios} alCambiar={(v) => cambiar("recordatorios", v)} /></div>
        {msg && <Alerta tono={msg.ok ? "ok" : "error"}>{msg.texto}</Alerta>}
      </div>
    </section>
  );
}

export default memo(AsistentePreferencias);
