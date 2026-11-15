import { Suspense, lazy, useEffect, useRef, useState, type CSSProperties } from "react";
import { api } from "../shared/api/client";
import Alerta from "../shared/components/Alerta";
import FondoEstrellas from "../shared/components/FondoEstrellas";
import tierra from "../shared/assets/tierra.webp";
import tierraMapa from "../shared/assets/tierra-mapa.jpg";
import Tierra3D from "../shared/components/Tierra3D";
import logoSpaceApps from "../shared/assets/spaceapps.png";
import { useTema } from "../shared/hooks/useTema";
import { SelectorTripulante, useTripulantes } from "../features/tripulantes";
import { MonitorPage, useEstadoTripulante } from "../features/monitor";
import { MonitorCabina, resolverAmbiente, useAlertasColectivas } from "../features/cabina";
import { AccesoTripulante, PerfilMenu, useAuth } from "../features/seguridad";
import { Bienvenida } from "../features/bienvenida";
import InstalarApp from "../shared/components/InstalarApp";
import { useTranslation } from "../i18n";
import CambioIdioma from "../shared/components/CambioIdioma";
import ToggleIdioma from "../shared/components/ToggleIdioma";
import ToggleTema from "../shared/components/ToggleTema";
import BarraLateral, { VISTAS } from "./BarraLateral";
import { useRuta } from "./useRuta";
import BarraSuperior from "./BarraSuperior";

// Vistas secundarias: se descargan solo al abrirlas
const BienestarPage = lazy(() => import("../features/bienestar").then((m) => ({ default: m.BienestarPage })));
const HistorialPage = lazy(() => import("../features/historial").then((m) => ({ default: m.HistorialPage })));
const SistemaPage = lazy(() => import("../features/sistema").then((m) => ({ default: m.SistemaPage })));
const BurbujaVoz = lazy(() => import("../features/voz").then((m) => ({ default: m.BurbujaVoz })));
const AsistentePage = lazy(() => import("../features/asistente").then((m) => ({ default: m.AsistentePage })));
const BandaPage = lazy(() => import("../features/banda").then((m) => ({ default: m.BandaPage })));
const RiesgosPage = lazy(() => import("../features/peligros").then((m) => ({ default: m.RiesgosPage })));
const EnlacePage = lazy(() => import("../features/enlace").then((m) => ({ default: m.EnlacePage })));

const estadoUmbral = (t: (k: string) => string, estado: string) => { const k = `prototype.estado.${estado}`; const r = t(k); return r === k ? estado : r; };

interface EstadoUmbrales { version: string; estado: string }

export default function App() {
  const { t } = useTranslation();
  const auth = useAuth();
  const { tripulantes, tid, setTid, error: errorTripulantes } = useTripulantes();
  useEffect(() => {
    if (auth.actor?.tripulante_id) setTid(auth.actor.tripulante_id);
  }, [auth.actor?.tripulante_id, setTid]);
  const { estado, error: errorEstado, refrescar } = useEstadoTripulante(auth.requiereAcceso ? "" : tid);
  const { tema, alternar } = useTema();
  const [vista, setVista] = useRuta();
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
  const orden = ["monitor", "banda", "historial", "bienestar", "asistente", "riesgos", "enlace", "sistema"];
  const previa = useRef(orden.indexOf(vista));
  const dx = orden.indexOf(vista) >= previa.current ? 32 : -32;
  useEffect(() => { previa.current = orden.indexOf(vista); });

  const aviso = umbrales && !umbrales.estado.startsWith("validado")
    ? { titulo: t("prototype.title"), texto: t("prototype.text", { version: umbrales.version, estado: estadoUmbral(t, umbrales.estado) }) } : null;
  useEffect(() => { api<EstadoUmbrales>("/umbrales").then(setUmbrales).catch(() => setUmbrales(null)); }, []);

  if (auth.requiereAcceso) {
    return (
      <>
        <FondoEstrellas />
        <CambioIdioma />
        <div className="acceso-barra"><ToggleIdioma /><ToggleTema tema={tema} alternar={alternar} /></div>
        <main className="acceso-pantalla">
          <div className="acceso-escena" aria-hidden="true">
            <Tierra3D className="acceso-esfera" mapa={tierraMapa} respaldo={tierra} />
            <img className="acceso-logo" src={logoSpaceApps} alt="" width="440" height="172" decoding="async" />
          </div>
          <AccesoTripulante
            tripulantes={tripulantes.map((t) => ({ valor: t.id, etiqueta: `${t.nombre} · ${t.rol}` }))}
            alEntrar={auth.login}
            alRecuperar={auth.recuperar}
          />
        </main>
      </>
    );
  }

  return (
    <>
      <FondoEstrellas />
      {tid && <Suspense fallback={null}><BurbujaVoz tripulanteId={tid} /></Suspense>}
      <CambioIdioma />
      <Bienvenida mostrarBotonFlotante={false} />
      <InstalarApp />
      <div className="app">
      <BarraLateral vista={vista} alCambiarVista={setVista} aviso={aviso} />
      <div className="app-col">
      <BarraSuperior
        tema={tema} alAlternarTema={alternar}
        selector={!auth.actor ? <SelectorTripulante tripulantes={tripulantes} valor={tid} alCambiar={setTid} /> : undefined}
        perfil={auth.actor ? (
          <PerfilMenu
            nombre={tripulantes.find((x) => x.id === tid)?.nombre ?? auth.actor.nombre ?? auth.actor.tripulante_id ?? ""}
            rol={tripulantes.find((x) => x.id === tid)?.rol ?? auth.actor.rol}
            id={tid}
            alSalir={auth.logout}
          />
        ) : undefined}
      />
      <main className="pantalla">
        <div className="avisos">
          {aviso && <div className="aviso-movil"><Alerta tono="aviso" titulo={aviso.titulo}>{aviso.texto}</Alerta></div>}
          {error && <Alerta tono="error" titulo={t("errors.generic")}>{error}</Alerta>}
        </div>
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
            {tid && vista === "asistente" && <AsistentePage tripulanteId={tid} />}
            {tid && vista === "banda" && <BandaPage tripulanteId={tid} estado={estado} refrescar={refrescar} />}
            {tid && vista === "historial" && <HistorialPage tripulanteId={tid} estado={estado} />}
            {vista === "riesgos" && <RiesgosPage />}
            {vista === "sistema" && <SistemaPage />}
            {vista === "enlace" && <EnlacePage />}
          </Suspense>
        </div>
      </main>
      </div>
      </div>
    </>
  );
}
