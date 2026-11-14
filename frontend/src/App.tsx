import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type { Estado, Tripulante } from "./api/tipos";
import FiguraHumana from "./components/FiguraHumana";
import PanelMedicion from "./components/PanelMedicion";
import DiarioTripulante from "./components/DiarioTripulante";
import Tamizaje from "./components/Tamizaje";
import ConsolaEnlace from "./components/ConsolaEnlace";

interface EstadoUmbrales { version: string; estado: string }

type Vista = "monitor" | "bienestar" | "enlace";

export default function App() {
  const [tripulantes, setTripulantes] = useState<Tripulante[]>([]);
  const [tid, setTid] = useState("");
  const [vista, setVista] = useState<Vista>("monitor");
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState("");
  const [umbrales, setUmbrales] = useState<EstadoUmbrales | null>(null);

  useEffect(() => {
    api<Tripulante[]>("/tripulantes")
      .then((t) => { setTripulantes(t); if (t[0]) setTid(t[0].id); })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  const refrescar = useCallback(() => {
    if (tid) api<Estado>(`/estado/${tid}`).then(setEstado).catch((e) => setError(e.message));
  }, [tid]);
  useEffect(() => { refrescar(); }, [refrescar]);

  return (
    <main>
      <header>
        <h1>ORBIT Health</h1>
        <select value={tid} onChange={(e) => setTid(e.target.value)} aria-label="Tripulante">
          {tripulantes.map((t) => <option key={t.id} value={t.id}>{t.nombre} · {t.rol}</option>)}
        </select>
      </header>
      {umbrales && !umbrales.estado.startsWith("validado") && (
        <p className="aviso">Prototipo de apoyo, no sustituye criterio médico. Umbrales v{umbrales.version}: {umbrales.estado}.</p>
      )}
      {error && <p className="error">{error}</p>}
      <nav>
        {(["monitor", "bienestar", "enlace"] as Vista[]).map((v) => (
          <button key={v} className={vista === v ? "activo" : ""} onClick={() => setVista(v)}>
            {v === "monitor" ? "Monitor" : v === "bienestar" ? "Bienestar" : "Enlace"}
          </button>
        ))}
      </nav>
      {tid && vista === "monitor" && (
        <div className="grid">
          <FiguraHumana lecturas={estado?.indicadores ?? []} />
          <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
          <section className="panel">
            <h2>Resumen</h2>
            <p>NEWS2 (ventana {estado?.ventana_min ?? "–"} min): <strong>{estado?.news2.puntos ?? 0}</strong>{" "}
              <span className={`badge ${estado?.nivel_general ?? "sin_datos"}`}>{estado?.nivel_general ?? "sin datos"}</span></p>
            {estado && estado.news2.faltantes.length > 0 && (
              <p className="suave">Variables NEWS2 sin dato reciente: {estado.news2.faltantes.join(", ")}. El puntaje puede estar subestimado.</p>
            )}
            {estado?.indicadores.map((i) => (
              <div key={i.indicador} className="item">{i.indicador}: {i.valor} {i.unidad} <span className={`badge ${i.nivel}`}>{i.nivel}</span></div>
            ))}
          </section>
        </div>
      )}
      {tid && vista === "bienestar" && (
        <div className="grid"><DiarioTripulante tripulanteId={tid} /><Tamizaje tripulanteId={tid} /></div>
      )}
      {vista === "enlace" && <ConsolaEnlace />}
    </main>
  );
}
