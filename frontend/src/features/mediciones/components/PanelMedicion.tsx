import { FormEvent, memo, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta, { type TonoAlerta } from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import Selector from "../../../shared/components/Selector";
import type { IndicadorDef, RespuestaLectura } from "../types/medicion";

const AVPU = ["A · Alerta", "V · Voz", "P · Dolor", "U · Sin respuesta"];
const TONO: Record<string, TonoAlerta> = { verde: "ok", amarillo: "aviso", rojo: "error" };

type Resultado = { error: string } | { lectura: RespuestaLectura } | null;

/** Barra con el rango fisiologico aceptado y la posicion del valor escrito (verde dentro, roja fuera). */
function RangoValor({ def, valor }: { def: IndicadorDef; valor: string }) {
  const num = Number(valor);
  const hay = valor !== "" && !Number.isNaN(num);
  const fuera = hay && (num < def.min || num > def.max);
  const pos = hay ? Math.min(100, Math.max(0, ((num - def.min) / (def.max - def.min)) * 100)) : 0;
  return (
    <div className={`rango${fuera ? " fuera" : ""}`}>
      <div className="rango-pista" aria-hidden="true">{hay && <span className="rango-marca" style={{ left: `${pos}%` }} />}</div>
      <div className="rango-ext"><span>{def.min}</span><span className="rango-txt">{fuera ? "Fuera del rango fisiológico" : "Rango fisiológico aceptado"}</span><span>{def.max} {def.unidad}</span></div>
    </div>
  );
}

function PanelMedicion({ tripulanteId, alGuardar }: { tripulanteId: string; alGuardar: () => void }) {
  const [defs, setDefs] = useState<IndicadorDef[]>([]);
  const [clave, setClave] = useState("spo2");
  const [valor, setValor] = useState("");
  const [res, setRes] = useState<Resultado>(null);

  useEffect(() => { api<IndicadorDef[]>("/indicadores").then(setDefs).catch(() => setDefs([])); }, []);
  const def = defs.find((d) => d.clave === clave);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const num = Number(valor);
    if (valor === "" || Number.isNaN(num)) return setRes({ error: "Ingresa un número válido" });
    if (def && (num < def.min || num > def.max))
      return setRes({ error: `Fuera de rango fisiológico (${def.min}–${def.max} ${def.unidad})` });
    try {
      const lectura = await post<RespuestaLectura>("/lecturas", { tripulante_id: tripulanteId, indicador: clave, valor: num });
      setRes({ lectura });
      setValor("");
      alGuardar();
    } catch (err) {
      setRes({ error: (err as Error).message });
    }
  }

  const lectura = res && "lectura" in res ? res.lectura : null;
  const extras = lectura ? [lectura.observacion && "valor en observación", lectura.aviso_linea_base && "se aleja de tu línea base"].filter(Boolean).join(" · ") : "";

  return (
    <form onSubmit={enviar} className="formulario captura">
      <p className="suave">Registra una medición a mano. El nivel y la prioridad se calculan al guardar.</p>

      <div className="campo">
        <span className="campo-etiqueta">Indicador</span>
        <Selector
          etiqueta="Indicador" valor={clave} alCambiar={(v) => { setClave(v); setValor(""); setRes(null); }}
          opciones={defs.map((d) => ({ valor: d.clave, etiqueta: d.etiqueta.includes(`(${d.unidad})`) ? d.etiqueta : `${d.etiqueta} (${d.unidad})` }))}
        />
      </div>

      <div className="campo">
        <label className="campo-etiqueta" htmlFor="captura-valor">Valor</label>
        {clave === "avpu" ? (
          <Segmentado rejilla etiqueta="Nivel de conciencia" valor={valor} alCambiar={(v) => { setValor(v); setRes(null); }} opciones={AVPU.map((t, i) => ({ valor: String(i), etiqueta: t }))} />
        ) : (
          <>
            <div className="entrada-valor">
              <input id="captura-valor" type="number" inputMode="decimal" step="any" value={valor} onChange={(e) => { setValor(e.target.value); setRes(null); }}
                placeholder={def ? `${def.min}–${def.max}` : "0"} />
              {def && <span className="entrada-unidad">{def.unidad}</span>}
            </div>
            {def && <RangoValor def={def} valor={valor} />}
          </>
        )}
      </div>

      <button type="submit" className="btn-primario captura-enviar" disabled={valor === ""}>Registrar medición</button>

      {res && "error" in res && <Alerta tono="error">{res.error}</Alerta>}
      {lectura && (
        <Alerta tono={TONO[lectura.nivel] ?? "info"} titulo={`Registrado · nivel ${lectura.nivel}`}>
          NEWS2 {lectura.puntos_news2} · prioridad {lectura.prioridad}{extras ? ` · ${extras}` : ""}
        </Alerta>
      )}
    </form>
  );
}

export default memo(PanelMedicion);
