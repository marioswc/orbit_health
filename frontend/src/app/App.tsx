import { Suspense, lazy, useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../shared/api/client";
import Alerta from "../shared/components/Alerta";
import Drawer from "../shared/components/Drawer";
import FondoEstrellas from "../shared/components/FondoEstrellas";
import { useTema } from "../shared/hooks/useTema";
import { SelectorTripulante, useTripulantes } from "../features/tripulantes";
import { MonitorPage, useEstadoTripulante } from "../features/monitor";
import { PanelMedicion } from "../features/mediciones";
import { MonitorCabina, resolverAmbiente, useAlertasColectivas } from "../features/cabina";
import { AccesoTripulante, useAuth } from "../features/seguridad";
import BarraSuperior, { type Vista } from "./BarraSuperior";
import BotonCaptura from "./BotonCaptura";

// Vistas secundarias: se descargan solo al abrirlas
const BienestarPage = lazy(() => import("../features/bienestar").then((m) => ({ default: m.BienestarPage })));
const RiesgosPage = lazy(() => import("../features/peligros").then((m) => ({ default: m.RiesgosPage })));
const EnlacePage = lazy(() => import("../features/enlace").then((m) => ({ default: m.EnlacePage })));

interface EstadoUmbrales { version: string; estado: string }

/** Estado inicial desde la URL (?vista=enlace&captura=1): sirve para compartir o ensayar una pantalla de la demo. */
function desdeUrl() {
  const q = new URLSearchParams(window.location.search);
  const v = q.get("vista");
  return { vista: (v === "bienestar" || v === "enlace" || v === "riesgos" ? v : "monitor") as Vista, captura: q.get("captura") === "1" };
}

export default function App() {
  const auth = useAuth();
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(auth.requiereAcceso ? "" : tid);
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
  // Direccion del cambio de vista: el contenido entra desde el lado hacia el que se movio la pestana
  const orden = ["monitor", "bienestar", "riesgos", "enlace"];
  const previa = useRef(orden.indexOf(ini.vista));
  const dx = orden.indexOf(vista) >= previa.current ? 32 : -32;
  useEffect(() => { previa.current = orden.indexOf(vista); });
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
        selector={
          auth.requiereAcceso ? null : (
            <>
              <SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} />
              {auth.actor && (
                <button type="button" className="ghost" onClick={auth.logout} aria-label={`Cerrar sesión (${auth.actor.rol})`}>
                  Salir
                </button>
              )}
            </>
          )
        }
      />
      <main className="pantalla">
        <div className="avisos">
          {umbrales && !umbrales.estado.startsWith("validado") && (
            <Alerta tono="aviso" titulo="Prototipo de apoyo, no sustituye criterio médico">Umbrales v{umbrales.version}: {umbrales.estado}.</Alerta>
          )}
          {error && <Alerta tono="error" titulo="Algo salió mal">{error}</Alerta>}
        </div>
        {auth.requiereAcceso ? (
          <AccesoTripulante
            tripulantes={tripulantes.map((t) => ({ valor: t.id, etiqueta: `${t.nombre} · ${t.rol}` }))}
            alEntrar={auth.login}
            alRecuperar={auth.recuperar}
          />
        ) : (
        <div className="vista" key={vista} style={{ display: vista === "monitor" ? "contents" : undefined, "--dx": `${dx}px` } as CSSProperties}>
          {tid && vista === "monitor" && (
            <MonitorPage
              tripulanteId={tid}
              estado={estado}
              ambiente={ambiente.nivel}
              cabina={<MonitorCabina ambiente={ambiente} alerta={colectivas?.alertas[0] ?? null} />}
            />
          )}
          <Suspense fallback={<span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}>
            {tid && vista === "bienestar" && <BienestarPage tripulanteId={tid} />}
            {vista === "riesgos" && <RiesgosPage />}
            {vista === "enlace" && <EnlacePage />}
          </Suspense>
        </div>
        )}
      </main>
      </div>

      {!auth.requiereAcceso && !captura && <BotonCaptura alAbrir={abrirCaptura} disponible={!!tid} />}
      <Drawer abierto={!auth.requiereAcceso && captura && !!tid} alCerrar={cerrarCaptura} titulo="Captura manual">
        <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
      </Drawer>
    </>
  );
}
