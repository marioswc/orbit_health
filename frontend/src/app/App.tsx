import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import { api } from "../shared/api/client";
import Alerta from "../shared/components/Alerta";
import Drawer from "../shared/components/Drawer";
import FondoEstrellas from "../shared/components/FondoEstrellas";
import { useTema } from "../shared/hooks/useTema";
import { SelectorTripulante, useTripulantes } from "../features/tripulantes";
import { MonitorPage, useEstadoTripulante } from "../features/monitor";
import { PanelMedicion } from "../features/mediciones";
import { MonitorCabina, resolverAmbiente, useAlertasColectivas } from "../features/cabina";
import BarraSuperior, { type Vista } from "./BarraSuperior";
import BotonCaptura from "./BotonCaptura";

// Vistas secundarias: se descargan solo al abrirlas
const BienestarPage = lazy(() => import("../features/bienestar").then((m) => ({ default: m.BienestarPage })));
const EnlacePage = lazy(() => import("../features/enlace").then((m) => ({ default: m.EnlacePage })));

interface EstadoUmbrales { version: string; estado: string }

/** Estado inicial desde la URL (?vista=enlace&captura=1): sirve para compartir o ensayar una pantalla de la demo. */
function desdeUrl() {
  const q = new URLSearchParams(window.location.search);
  const v = q.get("vista");
  return { vista: (v === "bienestar" || v === "enlace" ? v : "monitor") as Vista, captura: q.get("captura") === "1" };
}

export default function App() {
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(tid);
  const { tema, alternar } = useTema();
  const [ini] = useState(desdeUrl);
  const [vista, setVista] = useState<Vista>(ini.vista);
  const [captura, setCaptura] = useState(ini.captura);
  const [umbrales, setUmbrales] = useState<EstadoUmbrales | null>(null);
  const error = errorTripulantes || errorEstado;
  const { datos: colectivas } = useAlertasColectivas(estado);
  // La cabina se compone aqui (una feature no importa de otra): lecturas ya clasificadas por el backend
  const ambiente = resolverAmbiente(
    colectivas,
    estado?.indicadores.find((i) => i.indicador === "co2") ?? null,
    estado?.indicadores.find((i) => i.indicador === "dosis_pct") ?? null,
  );
  const cerrarCaptura = useCallback(() => setCaptura(false), []);
  const abrirCaptura = useCallback(() => setCaptura(true), []);

  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  return (
    <>
      <FondoEstrellas />
      <div className="app">
      <BarraSuperior
        vista={vista} alCambiarVista={setVista}
        tema={tema} alAlternarTema={alternar}
        selector={<SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} />}
      />
      <main className="pantalla">
        <div className="avisos">
          {umbrales && !umbrales.estado.startsWith("validado") && (
            <Alerta tono="aviso" titulo="Prototipo de apoyo, no sustituye criterio médico">Umbrales v{umbrales.version}: {umbrales.estado}.</Alerta>
          )}
          {error && <Alerta tono="error" titulo="Algo salió mal">{error}</Alerta>}
        </div>
        <div className="vista" key={vista} style={{ display: vista === "monitor" ? "contents" : undefined }}>
          {tid && vista === "monitor" && (
            <MonitorPage
              estado={estado}
              alAbrirCaptura={abrirCaptura}
              ambiente={ambiente.nivel}
              cabina={<MonitorCabina ambiente={ambiente} alerta={colectivas?.alertas[0] ?? null} />}
            />
          )}
          <Suspense fallback={<span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}>
            {tid && vista === "bienestar" && <BienestarPage tripulanteId={tid} />}
            {vista === "enlace" && <EnlacePage />}
          </Suspense>
        </div>
      </main>
      </div>

      {!captura && <BotonCaptura alAbrir={abrirCaptura} disponible={!!tid} />}
      <Drawer abierto={captura && !!tid} alCerrar={cerrarCaptura} titulo="Captura manual">
        <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
      </Drawer>
    </>
  );
}
