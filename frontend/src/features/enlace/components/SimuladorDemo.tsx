import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";
import type { ComparativaOrbit, EscenarioDemo } from "../types/cola";

interface EstadoSimulacionViva {
  activa: boolean;
  finalizada: boolean;
  minuto_mision: number;
  duracion_min: number;
  progreso_pct: number;
  eventos: { minuto?: number; texto?: string; tipo?: string }[];
  hitos: Record<string, unknown>;
}

const PERFILES = ["luna", "marte_cercano", "marte_medio", "marte"] as const;

function formatoTiempo(s: number): string {
  if (s === 0) return "0 s";
  if (s < 60) return `${s} s`;
  return `${Math.round((s / 60) * 10) / 10} min`;
}

/** Escenarios guionizados y linea de tiempo comparativa con y sin ORBIT. */
function SimuladorDemo() {
  const { t } = useTranslation("enlace");
  const perfiles = PERFILES.map((v) => ({ valor: v, etiqueta: t(`env.short.${v}`) }));
  const nivel = (n: string) => (["verde", "amarillo", "rojo", "sin_datos"].includes(n) ? t(`common:status.${n}`) : n);
  const [escenarios, setEscenarios] = useState<EscenarioDemo[]>([]);
  const [entorno, setEntorno] = useState("marte");
  const [comp, setComp] = useState<ComparativaOrbit | null>(null);
  const [resultado, setResultado] = useState<{ escenario: string; pasos: { paso: string; nivel?: string; prioridad?: number; despachados?: number }[] } | null>(null);
  const [sensorRes, setSensorRes] = useState<{ perfil: string; rondas: { ronda: number; nivel: string; puntos_news2: number }[]; primera_ronda_amarillo: number | null; primera_ronda_rojo: number | null } | null>(null);
  const [simViva, setSimViva] = useState<EstadoSimulacionViva | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<EscenarioDemo[]>("/demo/escenarios").then(setEscenarios).catch(() => {});
    api<EstadoSimulacionViva>("/demo/simulacion/estado").then(setSimViva).catch(() => {});
  }, []);

  useEffect(() => {
    if (!simViva?.activa) return;
    const t = setInterval(() => {
      api<EstadoSimulacionViva>("/demo/simulacion/estado").then(setSimViva).catch(() => {});
    }, 1500);
    return () => clearInterval(t);
  }, [simViva?.activa]);

  useEffect(() => {
    api<ComparativaOrbit>(`/demo/comparativa?entorno=${encodeURIComponent(entorno)}`)
      .then((d) => { setComp(d); setError(""); })
      .catch((e) => setError((e as Error).message));
  }, [entorno]);

  async function correr(id: string, reconectar: boolean) {
    setError("");
    try {
      const r = await post<NonNullable<typeof resultado>>(`/demo/escenarios/${encodeURIComponent(id)}?reconectar=${reconectar}`, {});
      setResultado(r);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function correrSensor(perfil: string) {
    setError("");
    try {
      const r = await post<NonNullable<typeof sensorRes>>(`/demo/sensor/T1?perfil=${encodeURIComponent(perfil)}`, {});
      setSensorRes(r);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function iniciarMisionViva() {
    setError("");
    try {
      await post("/demo/simulacion/iniciar", {});
      const s = await api<EstadoSimulacionViva>("/demo/simulacion/estado");
      setSimViva(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function detenerMisionViva() {
    setError("");
    try {
      await post("/demo/simulacion/detener", {});
      const s = await api<EstadoSimulacionViva>("/demo/simulacion/estado");
      setSimViva(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="demo-bloque">
      {comp && (
        <section className="tarjeta pieza comparativa" aria-label={t("demo.cmp.aria")}>
          <div className="comparativa-cab">
            <div>
              <h2>{t("demo.cmp.title", { evento: comp.evento })}</h2>
              <p className="suave">
                {t("demo.cmp.window")} <strong>{comp.ventana_sin_apoyo_min} min</strong> ({comp.ventana_sin_apoyo_s} s).
              </p>
            </div>
            <Segmentado etiqueta={t("demo.cmp.env_aria")} opciones={perfiles} valor={entorno} alCambiar={setEntorno} />
          </div>

          <div className="comparativa-cols">
            <div className="comparativa-col con">
              <h3>{t("demo.cmp.with")}</h3>
              <ol>
                {comp.con_orbit.map((p, i) => (
                  <li key={i}>
                    <span className="t-mono">{formatoTiempo(p.t_s)}</span>
                    <span>{p.texto}</span>
                  </li>
                ))}
              </ol>
            </div>
            <div className="comparativa-col sin">
              <h3>{t("demo.cmp.without")}</h3>
              <ol>
                {comp.sin_orbit.map((p, i) => (
                  <li key={i}>
                    <span className="t-mono">{formatoTiempo(p.t_s)}</span>
                    <span>{p.texto}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <p className="fuente">{comp.aviso}</p>
        </section>
      )}

      {escenarios.length > 0 && (
        <section className="tarjeta pieza escenarios" aria-label={t("demo.sc.aria")}>
          <h2>{t("demo.sc.title")}</h2>
          <p className="suave">{t("demo.sc.desc")}</p>
          <div className="escenarios-lista">
            {escenarios.map((e) => (
              <div key={e.id} className="escenario-item">
                <div>
                  <strong>{e.id.replace(/_/g, " ")}</strong>
                  <p className="suave">{e.descripcion}</p>
                </div>
                <div className="fila">
                  <button type="button" onClick={() => correr(e.id, false)}>{t("demo.sc.run")}</button>
                  <button type="button" className="ghost" onClick={() => correr(e.id, true)}>{t("demo.sc.run_reconnect")}</button>
                </div>
              </div>
            ))}
          </div>

          {resultado && (
            <div className="escenario-res">
              <strong>{t("demo.sc.last", { nombre: resultado.escenario })}</strong>
              <ul>
                {resultado.pasos.map((p, idx) => (
                  <li key={idx}>
                    <span>{p.paso}</span>
                    {p.nivel && <span className={`badge ${p.nivel}`}>{nivel(p.nivel)}</span>}
                    {p.despachados !== undefined && <span className="suave">{t("demo.sc.dispatched", { n: p.despachados })}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="tarjeta pieza escenarios" aria-label={t("demo.sensor.title")}>
        <div className="tierra-cab">
          <div>
            <h2>{t("demo.sensor.title")}</h2>
            <p className="suave">{t("demo.sensor.desc")}</p>
          </div>
          <div className="fila" style={{ flexWrap: "wrap" }}>
            <button type="button" onClick={() => correrSensor("deterioro_respiratorio")}>{t("demo.sensor.worsen")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("proceso_infeccioso")}>{t("demo.sensor.infection")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("intolerancia_ortostatica")}>{t("demo.sensor.orthostatic")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("exposicion_radiacion")}>{t("demo.sensor.radiation")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("hipoglucemia")}>{t("demo.sensor.hypoglycemia")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("hipoxia_ambiental_o2")}>{t("demo.sensor.o2")}</button>
            <button type="button" className="ghost" onClick={() => correrSensor("estable")}>{t("demo.sensor.stable")}</button>
          </div>
        </div>
        {sensorRes && (
          <div className="escenario-res">
            <strong>{t("demo.sensor.rounds", { n: sensorRes.rondas.length, perfil: sensorRes.perfil.replace(/_/g, " ") })}</strong>
            <span className="suave" style={{ marginLeft: 8 }}>
              {t("demo.sensor.first", { y: sensorRes.primera_ronda_amarillo ?? "—", r: sensorRes.primera_ronda_rojo ?? "—" })}
            </span>
          </div>
        )}
      </section>

      <section className="tarjeta pieza escenarios" aria-label="Misión simulada en vivo">
        <div className="tierra-cab">
          <div>
            <h2>Misión simulada en vivo</h2>
            <p className="suave">Las bandas envían solas, el enlace se corta en eclipse y vuelve con prioridad.</p>
          </div>
          <div className="fila">
            {!simViva?.activa ? (
              <button type="button" onClick={iniciarMisionViva}>Iniciar misión en vivo</button>
            ) : (
              <button type="button" className="ghost" onClick={detenerMisionViva}>Detener simulación</button>
            )}
          </div>
        </div>
        {simViva && (simViva.activa || simViva.finalizada || (simViva.eventos?.length ?? 0) > 0) && (
          <div className="escenario-res">
            <div className="tierra-cab">
              <strong>Minuto {simViva.minuto_mision} / {simViva.duracion_min} min ({simViva.progreso_pct}%)</strong>
              <span className={`badge ${simViva.activa ? "amarillo" : "verde"}`}>
                {simViva.activa ? "En curso" : simViva.finalizada ? "Finalizada" : "Detenida"}
              </span>
            </div>
            {(simViva.eventos?.length ?? 0) > 0 && (
              <ul>
                {(simViva.eventos ?? []).slice(-6).reverse().map((ev, idx) => (
                  <li key={idx}>
                    {ev.minuto !== undefined && <span className="t-mono">T+{ev.minuto}m</span>}
                    <span>{ev.texto ?? JSON.stringify(ev)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      {error && <Alerta tono="error" titulo={t("demo.error")}>{error}</Alerta>}
    </div>
  );
}

export default memo(SimuladorDemo);

