import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation, type Vars } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Segmentado from "../../../shared/components/Segmentado";
import { nivelActual } from "../../../shared/rendimiento";
import type { Cola, InfoLatencia, ItemCola } from "../types/cola";

const INTERVALO_MS = { alto: 2000, medio: 4000, bajo: 8000 } as const;

const PRIORIDADES = [
  { p: 1, nivel: "rojo" },
  { p: 2, nivel: "amarillo" },
  { p: 3, nivel: "verde" },
] as const;
const ENTORNOS = ["luna", "marte_cercano", "marte_medio", "marte"] as const;
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

/** "LECTURA_PRESION_DIASTOLICA" -> "Lectura presion diastolica". */
export function textoTipo(t: string): string {
  const s = t.replace(/_/g, " ").toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Como textoTipo, pero usa la traduccion `tipo.<CODIGO>` si existe (el codigo viene del servidor). */
export function textoTipoT(t: (k: string, v?: Vars) => string, tipo: string): string {
  const k = `tipo.${tipo}`;
  const r = t(k);
  return r === k ? textoTipo(tipo) : r;
}

function ConsolaEnlace() {
  const { t } = useTranslation("enlace");
  const [cola, setCola] = useState<Cola | null>(null);
  const [cerradas, setCerradas] = useState<number[]>([]); // prioridades plegadas
  const alternarPrio = (p: number) => setCerradas((c) => (c.includes(p) ? c.filter((x) => x !== p) : [...c, p]));
  const [latencia, setLatencia] = useState<InfoLatencia | null>(null);
  const [verif, setVerif] = useState<{ ok: boolean; texto?: string; total?: number; evento?: number | null } | null>(null);
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
    const iv = setInterval(() => { if (!document.hidden) cargar(); }, INTERVALO_MS[nivelActual()]);
    const visible = () => { if (!document.hidden) cargar(); };
    document.addEventListener("visibilitychange", visible);
    return () => { clearInterval(iv); document.removeEventListener("visibilitychange", visible); };
  }, [cargar]);

  async function enlace(activo: boolean, entorno: string) {
    try { await post("/enlace", { activo, entorno }); cargar(true); } catch (e) { setError((e as Error).message); }
  }
  async function verificar() {
    try {
      const r = await api<{ valida: boolean; total: number; primer_invalido: number | null }>("/cola/verificar");
      setVerif(r.valida ? { ok: true, total: r.total } : { ok: false, evento: r.primer_invalido });
    } catch (e) { setVerif({ ok: false, texto: (e as Error).message }); }
  }

  const conteo = useMemo(() => {
    const c = { retenido: 0, en_transito: 0, recibido: 0 };
    for (const i of cola?.items ?? []) c[i.estado] += 1;
    return c;
  }, [cola]);

  const entornos = ENTORNOS.map((v) => ({ valor: v, etiqueta: t(`env.${v}`) }));
  const modos = [{ valor: "on", etiqueta: t("canal.on") }, { valor: "off", etiqueta: t("canal.off") }];
  if (!cola) {
    return (
      <>
        <EncabezadoPagina etiqueta={t("kicker")} titulo={t("title")} descripcion={t("desc")} />
        {error ? <Alerta tono="error" titulo={t("load_error")}>{error}</Alerta> : <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      </>
    );
  }
  const { activo, entorno } = cola.enlace;

  return (
    <>
      <EncabezadoPagina etiqueta={t("kicker")} titulo={t("title")} descripcion={t("desc")}>
        <span className={`chip-estado ${activo ? "activo" : "eclipse"}`}>
          <span className={`latido${activo ? "" : " fijo"}`} aria-hidden="true" />
          {activo ? t("chip.active") : t("chip.eclipse")}
        </span>
      </EncabezadoPagina>

      {!activo && (
        <Alerta tono="aviso" titulo={t("eclipse.title")}>
          {t("eclipse.body")}
        </Alerta>
      )}

      <section className="kpis" aria-label={t("kpi.aria")}>
        {(["retenido", "en_transito", "recibido"] as const).map((k) => (
          <div key={k} className={`kpi ${k}${conteo[k] > 0 ? " hay" : ""}`}>
            <span className="kpi-icono">{IC_KPI[k]}</span>
            <span className="kpi-etiqueta">{t(`kpi.${k}`)}</span>
            <span className="kpi-valor">{conteo[k]}</span>
          </div>
        ))}
      </section>

      <section className="tarjeta pieza canal" aria-label={t("canal.aria")}>
        <div className="canal-viz" aria-hidden="true">
          <div className="nodo"><span className="nodo-icono">{IC_NAVE}</span>{t("canal.ship")}</div>
          <div className={`vinculo ${activo ? "on" : "off"}`}>
            <span className="vinculo-linea" /><span className="vinculo-pulso" /><span className="vinculo-pulso" /><span className="vinculo-pulso" />
            <span className="vinculo-corte">{IC_CORTE}</span>
            <span className="vinculo-retardo">{activo ? t("canal.delay", { valor: RETARDO[entorno] ?? "—" }) : t("canal.nolink")}</span>
          </div>
          <div className="nodo"><span className="nodo-icono">{IC_TIERRA}</span>{t("canal.earth")}</div>
        </div>
        {latencia && (
          <p className="suave latencia-detalle">
            {t("lat.roundtrip")} <strong>{Math.round(latencia.ida_y_vuelta_real_s / 60 * 10) / 10} min</strong> ({latencia.ida_y_vuelta_real_s} s)
            {" · "}{t("lat.simulated", { s: latencia.ida_y_vuelta_simulada_s, factor: latencia.factor_aceleracion })}
            {latencia.jitter_pct > 0 ? t("lat.jitter", { pct: latencia.jitter_pct }) : ""})
          </p>
        )}
        <div className="controles-enlace">
          <div className="campo">
            <span className="campo-etiqueta">{t("env.label")}</span>
            <Segmentado etiqueta={t("env.label")} opciones={entornos} valor={entorno} alCambiar={(v) => enlace(activo, v)} />
          </div>
          <div className="campo">
            <span className="campo-etiqueta">{t("canal.label")}</span>
            <Segmentado etiqueta={t("canal.state")} opciones={modos} valor={activo ? "on" : "off"} alCambiar={(v) => enlace(v === "on", entorno)} />
          </div>
        </div>
      </section>

      <section className="cols-prio" aria-label={t("prio.aria")}>
        {PRIORIDADES.map(({ p, nivel }) => {
          const items = cola.items.filter((i) => i.prioridad === p);
          return (
            <div key={p} className={`col-prioridad ${nivel}${cerradas.includes(p) ? " cerrada" : ""}`}>
              <button type="button" className="col-cab" aria-expanded={!cerradas.includes(p)} aria-controls={`prio-${p}`} onClick={() => alternarPrio(p)}>
                <span className="col-icono">{IC_PRIO[nivel]}</span>
                <span className="col-titulo"><strong>{t("prio.title", { n: p })}</strong><span className="suave">{t(`prio.${p}`)}</span></span>
                <span className="conteo" aria-label={t("prio.count", { count: items.length })}>{items.length}</span>
                <span className="col-flecha" aria-hidden="true" />
              </button>
              <div className="col-cuerpo" id={`prio-${p}`}><div className="col-cuerpo-int">
              {items.length === 0 ? <p className="vacio">{IC_VACIO}{t("prio.empty")}</p> : (
                <ul>
                  {items.slice(0, 8).map((i) => (
                    <li key={i.id}>
                      <span className="id-mono">#{i.id}</span>
                      <span className="tipo" title={i.tipo_evento}>{textoTipoT(t, i.tipo_evento)}</span>
                      <span className={`estado-cola ${i.estado}`}>{i.confirmado ? t("estado.confirmado") : t(`estado.${i.estado}`)}</span>
                    </li>
                  ))}
                </ul>
              )}
              </div></div>
            </div>
          );
        })}
      </section>

      <section className="tarjeta pieza verificacion">
        <div className="verificacion-fila">
          <div className="verificacion-info">
            <span className="alerta-icono">{IC_ESCUDO}</span>
            <div>
              <h2>{t("verif.title")}</h2>
              <p className="suave">{t("verif.desc")}</p>
            </div>
          </div>
          <button type="button" onClick={verificar}>{t("verif.button")}</button>
        </div>
        {verif && <Alerta tono={verif.ok ? "ok" : "error"} titulo={verif.ok ? t("verif.ok") : t("verif.fail")}>{verif.texto ?? (verif.ok ? t("verif.intact", { total: verif.total }) : t("verif.broken", { n: verif.evento ?? "" }))}</Alerta>}
      </section>
      {error && <Alerta tono="error" titulo={t("action_error")}>{error}</Alerta>}
    </>
  );
}

export default memo(ConsolaEnlace);
