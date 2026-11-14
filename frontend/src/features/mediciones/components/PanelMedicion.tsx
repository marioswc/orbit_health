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
    <section className="tarjeta">
      <h2>Captura manual</h2>
      <form onSubmit={enviar}>
        <div className="fila">
          <Selector
            etiqueta="Indicador" valor={clave} alCambiar={(v) => { setClave(v); setValor(""); }}
            opciones={defs.map((d) => ({ valor: d.clave, etiqueta: `${d.etiqueta} (${d.unidad})` }))}
          />
          {clave === "avpu" ? (
            <Selector etiqueta="Nivel de conciencia" valor={valor} alCambiar={setValor} opciones={AVPU.map((t, i) => ({ valor: String(i), etiqueta: t }))} />
          ) : (
            <input type="number" step="any" value={valor} onChange={(e) => setValor(e.target.value)}
              placeholder={def ? `${def.min}–${def.max}` : ""} aria-label="Valor" />
          )}
        </div>
        <button type="submit" className="btn-primario">Registrar</button>
      </form>
      {msg && <p className={msg.ok ? "ok" : "error"} style={{ marginTop: 16 }} role="status">{msg.texto}</p>}
    </section>
  );
}

export default memo(PanelMedicion);
