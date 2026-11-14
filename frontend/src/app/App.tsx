import { useEffect, useState } from "react";
import { api } from "../shared/api/client";
import { SelectorTripulante, useTripulantes } from "../features/tripulantes";
import { MonitorPage, useEstadoTripulante } from "../features/monitor";
import { PanelMedicion } from "../features/mediciones";
import { BienestarPage } from "../features/bienestar";
import { EnlacePage } from "../features/enlace";

interface EstadoUmbrales { version: string; estado: string }

type Vista = "monitor" | "bienestar" | "enlace";
const ETIQUETAS: Record<Vista, string> = { monitor: "Monitor", bienestar: "Bienestar", enlace: "Enlace" };

export default function App() {
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(tid);
  const [vista, setVista] = useState<Vista>("monitor");
  const [umbrales, setUmbrales] = useState<EstadoUmbrales | null>(null);
  const error = errorTripulantes || errorEstado;

  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  return (
    <main>
      <header>
        <h1>ORBIT Health</h1>
        <SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} />
      </header>
      {umbrales && !umbrales.estado.startsWith("validado") && (
        <p className="aviso">Prototipo de apoyo, no sustituye criterio médico. Umbrales v{umbrales.version}: {umbrales.estado}.</p>
      )}
      {error && <p className="error">{error}</p>}
      <nav>
        {(Object.keys(ETIQUETAS) as Vista[]).map((v) => (
          <button key={v} className={vista === v ? "activo" : ""} onClick={() => setVista(v)}>{ETIQUETAS[v]}</button>
        ))}
      </nav>
      {tid && vista === "monitor" && (
        <MonitorPage estado={estado}>
          <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
        </MonitorPage>
      )}
      {tid && vista === "bienestar" && <BienestarPage tripulanteId={tid} />}
      {vista === "enlace" && <EnlacePage />}
    </main>
  );
}
