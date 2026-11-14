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
import { useTranslation } from "../i18n";
import { CapturaContext } from "../shared/capturaContext";
import CambioIdioma from "../shared/components/CambioIdioma";
import BarraLateral, { VISTAS } from "./BarraLateral";
import { useRuta } from "./useRuta";
import BarraSuperior from "./BarraSuperior";
import BotonCaptura from "./BotonCaptura";

// Vistas secundarias: se descargan solo al abrirlas
const BienestarPage = lazy(() => import("../features/bienestar").then((m) => ({ default: m.BienestarPage })));
const HistorialPage = lazy(() => import("../features/historial").then((m) => ({ default: m.HistorialPage })));
const SistemaPage = lazy(() => import("../features/sistema").then((m) => ({ default: m.SistemaPage })));
const BandaPage = lazy(() => import("../features/banda").then((m) => ({ default: m.BandaPage })));
const RiesgosPage = lazy(() => import("../features/peligros").then((m) => ({ default: m.RiesgosPage })));
const EnlacePage = lazy(() => import("../features/enlace").then((m) => ({ default: m.EnlacePage })));

const estadoUmbral = (t: (k: string) => string, estado: string) => { const k = `prototype.estado.${estado}`; const r = t(k); return r === k ? estado : r; };

interface EstadoUmbrales { version: string; estado: string }

/** Estado inicial desde la URL (?captura=1): sirve para ensayar una pantalla de la demo. La vista va en la ruta (#/historial). */
const capturaDesdeUrl = () => new URLSearchParams(window.location.search).get("captura") === "1";

export default function App() {
  const { t } = useTranslation();
  const auth = useAuth();
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(auth.requiereAcceso ? "" : tid);
  const { tema, alternar } = useTema();
  const [vista, setVista] = useRuta();
  const [captura, setCaptura] = useState(capturaDesdeUrl);
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
  const orden = ["monitor", "banda", "historial", "bienestar", "riesgos", "enlace", "sistema"];
  const previa = useRef(orden.indexOf(vista));
  const dx = orden.indexOf(vista) >= previa.current ? 32 : -32;
  useEffect(() => { previa.current = orden.indexOf(vista); });
  const cerrarCaptura = useCallback(() => setCaptura(false), []);
  const abrirCaptura = useCallback(() => setCaptura(true), []);

  const aviso = umbrales && !umbrales.estado.startsWith("validado")
    ? { titulo: t("prototype.title"), texto: t("prototype.text", { version: umbrales.version, estado: estadoUmbral(t, umbrales.estado) }) } : null;
  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  return (
    <CapturaContext.Provider value={{ alAbrir: abrirCaptura, disponible: !!tid }}>
      <FondoEstrellas />
      <CambioIdioma />
      <div className="app">
      <BarraLateral vista={vista} alCambiarVista={setVista} aviso={aviso} />
      <div className="app-col">
      <BarraSuperior
        titulo={VISTAS.some((v) => v.id === vista) ? t(`nav.${vista}`) : undefined}
        tema={tema} alAlternarTema={alternar}
        selector={
          auth.requiereAcceso ? null : (
            <>
              <SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} />
              {auth.actor && (
                <button type="button" className="ghost" onClick={auth.logout} aria-label={t("topbar.logoutAria", { rol: auth.actor.rol })}>
                  {t("topbar.logout")}
                </button>
              )}
            </>
          )
        }
      />
      {!auth.requiereAcceso && !captura && <BotonCaptura alAbrir={abrirCaptura} disponible={!!tid} />}
      <main className="pantalla">
        <div className="avisos">
          {aviso && <div className="aviso-movil"><Alerta tono="aviso" titulo={aviso.titulo}>{aviso.texto}</Alerta></div>}
          {error && <Alerta tono="error" titulo={t("errors.generic")}>{error}</Alerta>}
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
            {tid && vista === "banda" && <BandaPage tripulanteId={tid} estado={estado} refrescar={refrescar} />}
            {tid && vista === "historial" && <HistorialPage tripulanteId={tid} estado={estado} />}
            {vista === "riesgos" && <RiesgosPage />}
            {vista === "sistema" && <SistemaPage />}
            {vista === "enlace" && <EnlacePage />}
          </Suspense>
        </div>
        )}
      </main>
      </div>
      </div>

      <Drawer abierto={!auth.requiereAcceso && captura && !!tid} alCerrar={cerrarCaptura} titulo="Captura manual">
        <PanelMedicion tripulanteId={tid} alGuardar={refrescar} />
      </Drawer>
    </CapturaContext.Provider>
  );
}
