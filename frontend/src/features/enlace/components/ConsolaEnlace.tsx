import { memo, useCallback, useEffect, useState } from "react";
import { api, post } from "../../../shared/api/client";
import type { Cola } from "../types/cola";

const NOMBRE = { 1: "Prioridad 1 · rojo", 2: "Prioridad 2 · amarillo", 3: "Prioridad 3 · verde" } as const;

function ConsolaEnlace() {
  const [cola, setCola] = useState<Cola | null>(null);
  const [verif, setVerif] = useState("");
  const [error, setError] = useState("");

  const cargar = useCallback(() => api<Cola>("/cola").then(setCola).catch((e) => setError(e.message)), []);
  useEffect(() => {
    cargar();
    // no consulta mientras la pestana esta oculta
    const t = setInterval(() => { if (!document.hidden) cargar(); }, 2000);
    const visible = () => { if (!document.hidden) cargar(); };
    document.addEventListener("visibilitychange", visible);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", visible); };
  }, [cargar]);

  async function enlace(activo: boolean, entorno: string) {
    try { await post("/enlace", { activo, entorno }); cargar(); } catch (e) { setError((e as Error).message); }
  }
  async function verificar() {
    const r = await api<{ valida: boolean; total: number; primer_invalido: number | null }>("/cola/verificar");
    setVerif(r.valida ? `Cadena íntegra (${r.total} eventos)` : `Cadena rota en evento ${r.primer_invalido}`);
  }

  if (!cola) return <section className="tarjeta"><h2>Cola y estado del canal</h2><p className="error">{error || "Cargando…"}</p></section>;
  const { activo, entorno } = cola.enlace;
  return (
    <section className="tarjeta">
      <h2>Cola y estado del canal</h2>
      <div className="fila">
        <button className={entorno === "luna" ? "activo" : ""} onClick={() => enlace(activo, "luna")}>Luna (1.3 s)</button>
        <button className={entorno === "marte" ? "activo" : ""} onClick={() => enlace(activo, "marte")}>Marte (1200 s)</button>
        <button className={activo ? "activo" : ""} onClick={() => enlace(true, entorno)}>Enlace normal</button>
        <button className={!activo ? "activo" : ""} onClick={() => enlace(false, entorno)}>Modo Eclipse</button>
      </div>
      <p>{activo ? <span className="ok"><span className="latido" />Enlace activo</span> : <span className="error"><span className="latido fijo" />Eclipse: nada sale de la nave</span>}</p>
      <div className="cols">
        {([1, 2, 3] as const).map((p) => (
          <div key={p} className="col-prio">
            <strong>{NOMBRE[p]}</strong>
            {cola.items.filter((i) => i.prioridad === p).slice(0, 8).map((i) => (
              <div key={i.id} className="item">#{i.id} {i.tipo_evento} · {i.estado}</div>
            ))}
          </div>
        ))}
      </div>
      <div className="fila" style={{ marginTop: 24 }}>
        <button onClick={verificar}>Verificar cadena de hash</button><span className="suave">{verif}</span>
      </div>
    </section>
  );
}

export default memo(ConsolaEnlace);
