import { Suspense, lazy, useEffect, useState } from "react";
import { api } from "../shared/api/client";
import Logo from "../shared/components/Logo";
import FondoEstrellas from "../shared/components/FondoEstrellas";
import ToggleTema from "../shared/components/ToggleTema";
import { useTema } from "../shared/hooks/useTema";
import { SelectorTripulante, useTripulantes } from "../features/tripulantes";
import { MonitorPage, useEstadoTripulante } from "../features/monitor";
import { PanelMedicion } from "../features/mediciones";

// Vistas secundarias: se descargan solo al abrirlas
const BienestarPage = lazy(() => import("../features/bienestar").then((m) => ({ default: m.BienestarPage })));
const EnlacePage = lazy(() => import("../features/enlace").then((m) => ({ default: m.EnlacePage })));

interface EstadoUmbrales { version: string; estado: string }

type Vista = "monitor" | "bienestar" | "enlace";
const ETIQUETAS: Record<Vista, string> = { monitor: "Monitor", bienestar: "Bienestar", enlace: "Enlace" };

export default function App() {
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(tid);
  const { tema, alternar } = useTema();
  const [vista, setVista] = useState<Vista>("monitor");
  const [umbrales, setUmbrales] = useState<EstadoUmbrales | null>(null);
  const error = errorTripulantes || errorEstado;

  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  return (
    <>
      <FondoEstrellas />
      <header className="barra">
        <div className="barra-interior">
          <span className="marca"><Logo />ORBIT Health</span>
          <nav aria-label="Vistas">
            {(Object.keys(ETIQUETAS) as Vista[]).map((v) => (
              <button key={v} className={`ghost ${vista === v ? "activo" : ""}`} aria-current={vista === v ? "page" : undefined} onClick={() => setVista(v)}>{ETIQUETAS[v]}</button>
            ))}
          </nav>
          <ToggleTema tema={tema} alternar={alternar} />
          <SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} />
        </div>
      </header>
      <main className="pantalla">
        <div className="avisos">
          {umbrales && !umbrales.estado.startsWith("validado") && (
            <p className="aviso">Prototipo de apoyo, no sustituye criterio médico. Umbrales v{umbrales.version}: {umbrales.estado}.</p>
          )}
          {error && <p className="error" role="alert">{error}</p>}
        </div>
        <div className="vista" key={vista} style={{ display: vista === "monitor" ? "contents" : undefined }}>
        {tid && vista === "monitor" && (
          <MonitorPage estado={estado}>
            <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
          </MonitorPage>
        )}
        <Suspense fallback={<span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}>
          {tid && vista === "bienestar" && <BienestarPage tripulanteId={tid} />}
          {vista === "enlace" && <EnlacePage />}
        </Suspense>
        </div>
      </main>
    </>
  );
}
