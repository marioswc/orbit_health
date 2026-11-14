import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Segmentado from "../../../shared/components/Segmentado";
import { nivelActual } from "../../../shared/rendimiento";
import type { Cola, InfoLatencia, ItemCola } from "../types/cola";

const INTERVALO_MS = { alto: 2000, medio: 4000, bajo: 8000 } as const;

const PRIORIDADES = [
  { p: 1, nivel: "rojo", titulo: "Prioridad 1", detalle: "Rojo · sale primero" },
  { p: 2, nivel: "amarillo", titulo: "Prioridad 2", detalle: "Amarillo" },
  { p: 3, nivel: "verde", titulo: "Prioridad 3", detalle: "Verde" },
] as const;
const ESTADOS: Record<ItemCola["estado"], string> = { retenido: "Retenido", en_transito: "En tránsito", recibido: "Recibido" };
const ENTORNOS = [
  { valor: "luna", etiqueta: "Luna · 1.3 s" },
  { valor: "marte_cercano", etiqueta: "Marte mín · 3 min" },
  { valor: "marte_medio", etiqueta: "Marte medio · 12.5 min" },
  { valor: "marte", etiqueta: "Marte máx · 20 min" },
];
const RETARDO: Record<string, string> = { luna: "1.3 s", marte_cercano: "180 s", marte_medio: "750 s", marte: "1200 s" };

const I = { width: 22, height: 22, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true } as const;
const IC_NAVE = <svg {...I} width={26} height={26}><path d="M12 3c3 2.5 4.5 6 4.5 9.5V16h-9v-3.5C7.5 9 9 5.5 12 3z" /><circle cx="12" cy="10" r="1.6" /><path d="M7.5 14 5 17.5l3-.5M16.5 14l2.5 3.5-3-.5M10 19.5c.5 1 1 1.5 2 2.5 1-1 1.5-1.5 2-2.5" /></svg>;
const IC_TIERRA = <svg {...I} width={26} height={26}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.6 2.6 4 5.7 4 9s-1.4 6.4-4 9c-2.6-2.6-4-5.7-4-9s1.4-6.4 4-9z" /></svg>;
const IC_CORTE = <svg {...I} width={16} height={16} strokeWidth={2}><path d="m6 6 12 12M18 6 6 18" /></svg>;
const IC_KPI = {
  retenido: <svg {...I}><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>,
  en_transito: <svg {...I}><path d="M4 12h13M13 7l5 5-5 5" /></svg>,
  recibido: <svg {...I}><path d="m5 12.5 4.2 4.2L19 7" /></svg>,
};
const IC_PRIO = {
  rojo: <svg {...I}><path d="M13 3 5 13.5h5.5L10 21l8-10.5h-5.5L13 3z" /></svg>,
  amarillo: <svg {...I}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></svg>,
  verde: <svg {...I}><path d="M12 3 4.5 6v5.5c0 4.4 3 7.9 7.5 9.5 4.5-1.6 7.5-5.1 7.5-9.5V6L12 3z" /><path d="m9 12 2.2 2.2L15.2 10" /></svg>,
};
const IC_ESCUDO = <svg {...I}><path d="M12 3 4.5 6v5.5c0 4.4 3 7.9 7.5 9.5 4.5-1.6 7.5-5.1 7.5-9.5V6L12 3z" /><path d="M9.5 12h5M12 9.5v5" /></svg>;
const IC_VACIO = <svg {...I} width={20} height={20}><path d="M4 13.5 6.5 5h11L20 13.5V19H4v-5.5zM4 13.5h4.5l1 2h5l1-2H20" /></svg>;
const ENLACE = [{ valor: "on", etiqueta: "Enlace normal" }, { valor: "off", etiqueta: "Modo Eclipse" }];

/** "LECTURA_PRESION_DIASTOLICA" -> "Lectura presion diastolica". */
export function textoTipo(t: string): string {
  const s = t.replace(/_/g, " ").toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function ConsolaEnlace() {
  const [cola, setCola] = useState<Cola | null>(null);
  const [latencia, setLatencia] = useState<InfoLatencia | null>(null);
  const [verif, setVerif] = useState<{ ok: boolean; texto: string } | null>(null);
  const [error, setError] = useState("");

  // Sin re-render si la respuesta es igual a la anterior (la cola casi nunca cambia entre consultas)
  const previa = useRef("");
  const enVuelo = useRef(false);
  const cargar = useCallback(async (forzar = false) => {
    if (enVuelo.current && !forzar) return; // no apila consultas si el servidor tarda
    enVuelo.current = true;
    try {
      const c = await api<Cola>("/cola");
      const huella = JSON.stringify(c);
      if (huella !== previa.current) { previa.current = huella; setCola(c); }
      api<InfoLatencia>("/enlace/latencia").then(setLatencia).catch(() => {});
      setError("");
    } catch (e) { setError((e as Error).message); } finally { enVuelo.current = false; }
  }, []);
  useEffect(() => {
    cargar();
    // no consulta mientras la pestana esta oculta; en equipos modestos, mas espaciado
    const t = setInterval(() => { if (!document.hidden) cargar(); }, INTERVALO_MS[nivelActual()]);
    const visible = () => { if (!document.hidden) cargar(); };
    document.addEventListener("visibilitychange", visible);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", visible); };
  }, [cargar]);

  async function enlace(activo: boolean, entorno: string) {
    try { await post("/enlace", { activo, entorno }); cargar(true); } catch (e) { setError((e as Error).message); }
  }
  async function verificar() {
    try {
      const r = await api<{ valida: boolean; total: number; primer_invalido: number | null }>("/cola/verificar");
      setVerif(r.valida ? { ok: true, texto: `Cadena íntegra (${r.total} eventos)` } : { ok: false, texto: `Cadena rota en el evento ${r.primer_invalido}` });
    } catch (e) { setVerif({ ok: false, texto: (e as Error).message }); }
  }

  const conteo = useMemo(() => {
    const c = { retenido: 0, en_transito: 0, recibido: 0 };
    for (const i of cola?.items ?? []) c[i.estado] += 1;
    return c;
  }, [cola]);

  if (!cola) {
    return (
      <>
        <EncabezadoPagina etiqueta="Enlace" titulo="Enlace con la Tierra" descripcion="Qué sale de la nave y en qué orden: primero lo más grave." />
        {error ? <Alerta tono="error" titulo="No se pudo cargar la cola">{error}</Alerta> : <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      </>
    );
  }
  const { activo, entorno } = cola.enlace;

  return (
    <>
      <EncabezadoPagina etiqueta="Enlace" titulo="Enlace con la Tierra" descripcion="Qué sale de la nave y en qué orden: primero lo más grave.">
        <span className={`chip-estado ${activo ? "activo" : "eclipse"}`}>
          <span className={`latido${activo ? "" : " fijo"}`} aria-hidden="true" />
          {activo ? "Enlace activo" : "Eclipse: nada sale"}
        </span>
      </EncabezadoPagina>

      {!activo && (
        <Alerta tono="aviso" titulo="Modo Eclipse activo">
          Los eventos quedan retenidos en la nave y saldrán en cuanto vuelva el enlace, primero los de mayor prioridad.
        </Alerta>
      )}

      <section className="kpis" aria-label="Resumen de la cola">
        {([["retenido", "Retenidos"], ["en_transito", "En tránsito"], ["recibido", "Recibidos"]] as const).map(([k, t]) => (
          <div key={k} className={`kpi ${k}${conteo[k] > 0 ? " hay" : ""}`}>
            <span className="kpi-icono">{IC_KPI[k]}</span>
            <span className="kpi-etiqueta">{t}</span>
            <span className="kpi-valor">{conteo[k]}</span>
          </div>
        ))}
      </section>

      <section className="tarjeta pieza canal" aria-label="Canal con la Tierra">
        <div className="canal-viz" aria-hidden="true">
          <div className="nodo"><span className="nodo-icono">{IC_NAVE}</span>Nave</div>
          <div className={`vinculo ${activo ? "on" : "off"}`}>
            <span className="vinculo-linea" /><span className="vinculo-pulso" /><span className="vinculo-pulso" /><span className="vinculo-pulso" />
            <span className="vinculo-corte">{IC_CORTE}</span>
            <span className="vinculo-retardo">{activo ? `retardo ${RETARDO[entorno] ?? "—"}` : "sin enlace"}</span>
          </div>
          <div className="nodo"><span className="nodo-icono">{IC_TIERRA}</span>Tierra</div>
        </div>
        {latencia && (
          <p className="suave latencia-detalle">
            Ida y vuelta real: <strong>{Math.round(latencia.ida_y_vuelta_real_s / 60 * 10) / 10} min</strong> ({latencia.ida_y_vuelta_real_s} s)
            {" · "}Simulado: {latencia.ida_y_vuelta_simulada_s} s (×{latencia.factor_aceleracion}
            {latencia.jitter_pct > 0 ? `, ±${latencia.jitter_pct}% jitter` : ""})
          </p>
        )}
        <div className="controles-enlace">
          <div className="campo">
            <span className="campo-etiqueta">Entorno</span>
            <Segmentado etiqueta="Entorno" opciones={ENTORNOS} valor={entorno} alCambiar={(v) => enlace(activo, v)} />
          </div>
          <div className="campo">
            <span className="campo-etiqueta">Canal</span>
            <Segmentado etiqueta="Estado del enlace" opciones={ENLACE} valor={activo ? "on" : "off"} alCambiar={(v) => enlace(v === "on", entorno)} />
          </div>
        </div>
      </section>

      <section className="cols-prio" aria-label="Cola por prioridad">
        {PRIORIDADES.map(({ p, nivel, titulo, detalle }) => {
          const items = cola.items.filter((i) => i.prioridad === p);
          return (
            <div key={p} className={`col-prioridad ${nivel}`}>
              <header>
                <span className="col-icono">{IC_PRIO[nivel]}</span>
                <span className="col-titulo"><strong>{titulo}</strong><span className="suave">{detalle}</span></span>
                <span className="conteo" aria-label={`${items.length} eventos`}>{items.length}</span>
              </header>
              {items.length === 0 ? <p className="vacio">{IC_VACIO}Sin eventos</p> : (
                <ul>
                  {items.slice(0, 8).map((i) => (
                    <li key={i.id}>
                      <span className="id-mono">#{i.id}</span>
                      <span className="tipo" title={i.tipo_evento}>{textoTipo(i.tipo_evento)}</span>
                      <span className={`estado-cola ${i.estado}`}>{i.confirmado ? "Confirmado" : ESTADOS[i.estado]}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </section>

      <section className="tarjeta pieza verificacion">
        <div className="verificacion-fila">
          <div className="verificacion-info">
            <span className="alerta-icono">{IC_ESCUDO}</span>
            <div>
              <h2>Integridad de la cola</h2>
              <p className="suave">Cada evento enlaza con el anterior mediante un hash; si alguno se altera, la cadena se rompe.</p>
            </div>
          </div>
          <button type="button" onClick={verificar}>Verificar cadena de hash</button>
        </div>
        {verif && <Alerta tono={verif.ok ? "ok" : "error"} titulo={verif.ok ? "Verificación correcta" : "Verificación fallida"}>{verif.texto}</Alerta>}
      </section>
      {error && <Alerta tono="error" titulo="No se pudo completar la acción">{error}</Alerta>}
    </>
  );
}

export default memo(ConsolaEnlace);
