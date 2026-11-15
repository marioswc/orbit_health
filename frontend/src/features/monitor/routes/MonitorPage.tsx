import { useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "../../../i18n";
import Contador from "../../../shared/components/Contador";
import AccionCaptura from "../../../shared/components/AccionCaptura";
import Selector from "../../../shared/components/Selector";
import Titular from "../../../shared/components/Titular";
import AccionesClinicas from "../components/AccionesClinicas";
import DetalleZona from "../components/DetalleZona";
import FiguraHumana from "../components/FiguraHumana";
import GraficaSerie from "../components/GraficaSerie";
import RachaMediciones from "../components/RachaMediciones";
import RecordatorioCaptura from "../components/RecordatorioCaptura";
import { AnilloNews2, PulsoCardiaco, SignosVitales } from "../components/TableroSignos";
import { useEntornos } from "../hooks/useEntornos";
import { useHistorialIndicador } from "../hooks/useHistorialIndicador";
import { useSeries } from "../hooks/useSeries";
import { useZonaSeleccionada } from "../hooks/useZonaSeleccionada";
import type { Estado, LecturaEstado } from "../types/estado";
import { CAPAS, ZONAS, nivelZona, type NivelZona } from "../zonas";

interface Props {
  tripulanteId?: string;
  estado: Estado | null;
  /** Monitor de cabina (feature cabina), compuesto desde app/: va en la columna derecha. */
  cabina?: ReactNode;
  /** Peor nivel del aire/radiacion de cabina, para marcar Cabeza y Respiratorio en la figura. */
  ambiente?: NivelZona | null;
}

const SIN_LECTURAS: LecturaEstado[] = []; // referencia estable: evita recalcular niveles en cada render
const LEYENDA = ["verde", "amarillo", "rojo", "sin_datos"] as const;
const ORDEN: Record<string, number> = { rojo: 0, amarillo: 1, verde: 2 };
const AMBIENTALES = ["co2", "dosis_pct"];

/** Pantalla principal: tablero de mision. Astronauta a la izquierda; signos con su tendencia, detalle de zona, NEWS2, pulso y cabina alrededor. */
export default function MonitorPage({ tripulanteId = "", estado, cabina, ambiente = null }: Props) {
  const { t } = useTranslation("monitor");
  const { t: tc } = useTranslation("consola");
  const { zona, acercado, capa, setCapa, elegir, alejar } = useZonaSeleccionada();
  const [meses, setMeses] = useState(0);
  const [entornoId, setEntornoId] = useState("nave_en_transito");
  const entornos = useEntornos();
  const entornoActual = entornos?.entornos[entornoId] ?? null;
  const nivel = estado?.nivel_general ?? "sin_datos";
  const lecturas = estado?.indicadores ?? SIN_LECTURAS;

  const vitales = useMemo(() => lecturas.filter((l) => !AMBIENTALES.includes(l.indicador)).sort((a, b) => (ORDEN[a.nivel] ?? 3) - (ORDEN[b.nivel] ?? 3)), [lecturas]);
  const claves = useMemo(() => vitales.slice(0, 8).map((l) => l.indicador), [vitales]);
  const series = useSeries(tripulanteId, claves);
  const fc = lecturas.find((l) => l.indicador === "frecuencia_cardiaca");
  const [elegido, setElegido] = useState<string | null>(null);
  const sel = elegido ?? vitales[0]?.indicador ?? null;
  const hist = useHistorialIndicador(tripulanteId, sel);

  return (
    <div className="vista">
      <div className="titulo-pagina">
        <div className="titulo-accion"><AccionCaptura /></div>
        {estado ? (
          <>
            <Titular key={nivel} titulo={t(`page.titular.${nivel}`)}>
              {t("page.news2Pre")} <Contador valor={estado.news2.puntos} /> {t("page.news2Post", { min: estado.ventana_min })}
            </Titular>
            <p style={{ marginTop: 16 }}>
              <span className={`badge ${nivel}`}>{t(`common:status.${nivel}`)}</span>
            </p>
            {estado.news2.faltantes.length > 0 && (
              <p className="suave">{t("page.news2Faltantes", { lista: estado.news2.faltantes.join(", ") })}</p>
            )}
          </>
        ) : (
          <div aria-busy="true" aria-label={t("page.cargando")}>
            <span className="esqueleto" style={{ width: "min(420px, 80%)", height: 52 }} />
            <span className="esqueleto" style={{ width: 260, height: 18, marginTop: 16 }} />
          </div>
        )}
      </div>

      <section className="tablero" aria-label={t("page.escenario")}>
        <div className="t-col t-izq">
          {estado && (
            <section className="panel consola-panel" aria-label="NEWS2">
              <h2>NEWS2</h2>
              <AnilloNews2 puntos={estado.news2.puntos} nivel={estado.news2.nivel} ventana={estado.ventana_min} />
            </section>
          )}
          <section className="panel consola-panel" aria-label={tc("pulse.title")}>
            <h2>{tc("pulse.title")}</h2>
            <PulsoCardiaco lectura={fc} />
          </section>
          {cabina}
          <section className="panel consola-panel t-ten" aria-label={tc("trend.title")}>
            <h2>{tc("trend.title")}</h2>
            {sel ? <GraficaSerie compacta serie={hist.serie} cargando={hist.cargando} error={hist.error} alCerrar={() => setElegido(null)} /> : <p className="suave">{tc("vitals.empty")}</p>}
          </section>
        </div>

        <div className="t-col t-cen">
          <section className="panel panel-detalle">
            <DetalleZona id={zona} lecturas={lecturas} capa={capa} meses={meses} alMeses={setMeses} entorno={entornoActual} />
          </section>
          <section className="panel consola-panel" aria-label={tc("vitals.title")}>
            <h2>{tc("vitals.title")}</h2>
            {estado ? <SignosVitales vitales={vitales} series={series} seleccionado={sel} alElegir={setElegido} /> : <span className="esqueleto" style={{ height: 200 }} aria-busy="true" />}
          </section>
          {estado && (
            <AccionesClinicas nivel={nivel} proximaCapturaMin={estado.proxima_captura_min} reglas={estado.reglas_combinadas} acciones={estado.acciones_sugeridas} />
          )}
          {tripulanteId && <RecordatorioCaptura tripulanteId={tripulanteId} estado={estado} />}
          {tripulanteId && <RachaMediciones tripulanteId={tripulanteId} estado={estado} />}
        </div>

        <div className="panel t-fig">
          <div className="centro">
            <FiguraHumana lecturas={lecturas} seleccionada={zona} acercado={acercado} capa={capa} meses={meses} alSeleccionar={elegir} alAlejar={alejar} ambiente={ambiente} />
          </div>
          {/* Controles debajo de la figura, compactos: la figura siempre queda a la vista */}
          <div className="fig-controles">
            <div className="fig-grupo">
              <span className="fig-etiqueta">{t("page.zonas")}</span>
              <div className="zonas-lista fig-zonas" role="group" aria-label={t("page.zonasAria")}>
                {ZONAS.map((z) => (
                  <button key={z.id} type="button" className={`tab ${nivelZona(z.indicadores, lecturas)} ${zona === z.id ? "activo" : ""}`} aria-pressed={zona === z.id} onClick={() => elegir(z.id)}>
                    {t(`zona.${z.id}.etiqueta`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="fig-fila">
              <div className="fig-grupo">
                <span className="fig-etiqueta">{t("page.capas")}</span>
                <div className="capas" role="group" aria-label={t("page.capasAria")}>
                  {CAPAS.map((c) => (
                    <button key={c.id} type="button" className={capa === c.id ? "activo" : ""} aria-pressed={capa === c.id} onClick={() => setCapa(c.id)}>{t(`capa.${c.id}`)}</button>
                  ))}
                </div>
              </div>
              {entornos && (
                <div className="fig-grupo">
                  <span className="fig-etiqueta">Entorno</span>
                  <Selector
                    etiqueta="Entorno de la misión" valor={entornoId ?? ""} alCambiar={setEntornoId}
                    opciones={Object.entries(entornos.entornos).map(([clave, ent]) => ({ valor: clave, etiqueta: `${ent.nombre}${ent.gravedad_g !== null ? ` (${ent.gravedad_g} g)` : ""}` }))}
                  />
                </div>
              )}
            </div>
          </div>
          <ul className="leyenda leyenda-pie" aria-label={t("page.leyendaAria")}>
            {LEYENDA.map((k) => <li key={k}><span className={`badge ${k}`}>{t(`page.leyenda.${k}`)}</span></li>)}
          </ul>
        </div>
      </section>
    </div>
  );
}
