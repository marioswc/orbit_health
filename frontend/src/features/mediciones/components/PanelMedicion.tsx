import { FormEvent, memo, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
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
    <section className="panel">
      <h2>Captura manual</h2>
      <form onSubmit={enviar}>
        <div className="fila">
          <select value={clave} onChange={(e) => { setClave(e.target.value); setValor(""); }}>
            {defs.map((d) => <option key={d.clave} value={d.clave}>{d.etiqueta} ({d.unidad})</option>)}
          </select>
          {clave === "avpu" ? (
            <select value={valor} onChange={(e) => setValor(e.target.value)}>
              <option value="">Selecciona…</option>
              {AVPU.map((t, i) => <option key={t} value={i}>{t}</option>)}
            </select>
          ) : (
            <input type="number" step="any" value={valor} onChange={(e) => setValor(e.target.value)}
              placeholder={def ? `${def.min}–${def.max}` : ""} aria-label="Valor" />
          )}
          <button type="submit">Registrar</button>
        </div>
      </form>
      {msg && <p className={msg.ok ? "ok" : "error"}>{msg.texto}</p>}
    </section>
  );
}

export default memo(PanelMedicion);
