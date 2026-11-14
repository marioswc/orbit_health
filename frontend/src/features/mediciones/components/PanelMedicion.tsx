import { FormEvent, memo, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Selector from "../../../shared/components/Selector";
import type { IndicadorDef, RespuestaLectura } from "../types/medicion";

const AVPU = ["A (alerta)", "V (voz)", "P (dolor)", "U (sin respuesta)"];

function PanelMedicion({ tripulanteId, alGuardar }: { tripulanteId: string; alGuardar: () => void }) {
  const [defs, setDefs] = useState<IndicadorDef[]>([]);
  const [clave, setClave] = useState("spo2");
  const [valor, setValor] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);

  useEffect(() => { api<IndicadorDef[]>("/indicadores").then(setDefs).catch(() => setDefs([])); }, []);
  const def = defs.find((d) => d.clave === clave);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const num = Number(valor);
    if (valor === "" || Number.isNaN(num)) return setMsg({ ok: false, texto: "Ingresa un número válido" });
    if (def && (num < def.min || num > def.max))
      return setMsg({ ok: false, texto: `Fuera de rango fisiológico (${def.min}–${def.max} ${def.unidad})` });
    try {
      const r = await post<RespuestaLectura>("/lecturas", { tripulante_id: tripulanteId, indicador: clave, valor: num });
      const extras = [r.observacion && "observación", r.aviso_linea_base && "desvío de línea base"].filter(Boolean).join(", ");
      setMsg({ ok: true, texto: `Nivel ${r.nivel} · NEWS2 ${r.puntos_news2} · prioridad ${r.prioridad}${extras ? " · " + extras : ""}` });
      setValor("");
      alGuardar();
    } catch (err) {
      setMsg({ ok: false, texto: (err as Error).message });
    }
  }

  return (
    <form onSubmit={enviar} className="formulario">
      <p className="suave">Registra una medición a mano. El nivel y la prioridad se calculan al guardar.</p>
      <div className="campo">
        <span className="campo-etiqueta">Indicador</span>
        <Selector
          etiqueta="Indicador" valor={clave} alCambiar={(v) => { setClave(v); setValor(""); setMsg(null); }}
          opciones={defs.map((d) => ({ valor: d.clave, etiqueta: `${d.etiqueta} (${d.unidad})` }))}
        />
      </div>
      <div className="campo">
        <label className="campo-etiqueta" htmlFor="captura-valor">Valor{def ? ` (${def.unidad})` : ""}</label>
        {clave === "avpu" ? (
          <Selector etiqueta="Nivel de conciencia" valor={valor} alCambiar={setValor} opciones={AVPU.map((t, i) => ({ valor: String(i), etiqueta: t }))} />
        ) : (
          <input id="captura-valor" type="number" step="any" value={valor} onChange={(e) => setValor(e.target.value)}
            placeholder={def ? `${def.min}–${def.max}` : ""} />
        )}
        {def && clave !== "avpu" && <span className="ayuda">Rango fisiológico aceptado: {def.min}–{def.max} {def.unidad}</span>}
      </div>
      <button type="submit" className="btn-primario">Registrar</button>
      {msg && <p className={`resultado ${msg.ok ? "ok" : "error"}`} role="status">{msg.texto}</p>}
    </form>
  );
}

export default memo(PanelMedicion);
