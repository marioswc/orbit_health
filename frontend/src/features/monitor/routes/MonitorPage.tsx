import { useState, type ReactNode } from "react";
import { useTranslation } from "../../../i18n";
import Contador from "../../../shared/components/Contador";
import Titular from "../../../shared/components/Titular";
import AccionesClinicas from "../components/AccionesClinicas";
import DetalleZona from "../components/DetalleZona";
import FiguraHumana from "../components/FiguraHumana";
import RachaMediciones from "../components/RachaMediciones";
import RecordatorioCaptura from "../components/RecordatorioCaptura";
import { useEntornos } from "../hooks/useEntornos";
import { useZonaSeleccionada } from "../hooks/useZonaSeleccionada";
import type { Estado, LecturaEstado } from "../types/estado";
import { CAPAS, ZONAS, nivelZona, type NivelZona } from "../zonas";

interface Props {
  tripulanteId?: string;
  estado: Estado | null;
  /** Monitor de cabina (feature cabina), compuesto desde app/: se muestra en la columna izquierda. */
  cabina?: ReactNode;
  /** Peor nivel del aire/radiacion de cabina, para marcar Cabeza y Respiratorio en la figura. */
  ambiente?: NivelZona | null;
}

const SIN_LECTURAS: LecturaEstado[] = []; // referencia estable: evita recalcular niveles en cada render
const LEYENDA = ["verde", "amarillo", "rojo", "sin_datos"] as const;

export default function MonitorPage({ tripulanteId = "", estado, cabina, ambiente = null }: Props) {
  const { t } = useTranslation("monitor");
  const { zona, acercado, capa, setCapa, elegir, alejar } = useZonaSeleccionada();
  const [meses, setMeses] = useState(0);
  const [entornoId, setEntornoId] = useState("nave_en_transito");
  const entornos = useEntornos();
  const entornoActual = entornos?.entornos[entornoId] ?? null;
  const nivel = estado?.nivel_general ?? "sin_datos";
  const lecturas = estado?.indicadores ?? SIN_LECTURAS;

  return (
    <div className="vista">
      <div className="titulo-pagina">
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


      <section className="escenario" aria-label={t("page.escenario")}>
        <aside className="lado izq">
          <div className="panel">
            <h2>{t("page.zonas")}</h2>
            <div className="zonas-lista" role="group" aria-label={t("page.zonasAria")}>
              {ZONAS.map((z) => (
                <button key={z.id} type="button" className={`tab ${nivelZona(z.indicadores, lecturas)} ${zona === z.id ? "activo" : ""}`} aria-pressed={zona === z.id} onClick={() => elegir(z.id)}>
                  {t(`zona.${z.id}.etiqueta`)}
                </button>
              ))}
            </div>
          </div>
          <div className="panel">
            <h2>{t("page.capas")}</h2>
            <div className="capas" role="group" aria-label={t("page.capasAria")}>
              {CAPAS.map((c) => (
                <button key={c.id} type="button" className={capa === c.id ? "activo" : ""} aria-pressed={capa === c.id} onClick={() => setCapa(c.id)}>{t(`capa.${c.id}`)}</button>
              ))}
            </div>
          </div>
          <div className="panel">
            <h2>{t("page.estados")}</h2>
            <ul className="leyenda" aria-label={t("page.leyendaAria")}>
              {LEYENDA.map((k) => <li key={k}><span className={`badge ${k}`}>{t(`page.leyenda.${k}`)}</span></li>)}
            </ul>
          </div>
          {entornos && (
            <div className="panel">
              <h2>Entorno</h2>
              <div className="capas" role="group" aria-label="Entorno de la misión">
                {Object.entries(entornos.entornos).map(([clave, ent]) => (
                  <button
                    key={clave}
                    type="button"
                    className={entornoId === clave ? "activo" : ""}
                    aria-pressed={entornoId === clave}
                    onClick={() => setEntornoId(clave)}
                  >
                    {ent.nombre}{ent.gravedad_g !== null ? ` (${ent.gravedad_g} g)` : ""}
                  </button>
                ))}
              </div>
            </div>
          )}
          {cabina}
        </aside>

        <div className="centro">
          <FiguraHumana lecturas={lecturas} seleccionada={zona} acercado={acercado} capa={capa} meses={meses} alSeleccionar={elegir} alAlejar={alejar} ambiente={ambiente} />
        </div>

        <aside className="lado der">
          <DetalleZona id={zona} lecturas={lecturas} capa={capa} meses={meses} alMeses={setMeses} entorno={entornoActual} />
        </aside>
      </section>

      {estado && (
        <AccionesClinicas
          nivel={nivel}
          proximaCapturaMin={estado.proxima_captura_min}
          reglas={estado.reglas_combinadas}
          acciones={estado.acciones_sugeridas}
        />
      )}
      {tripulanteId && <RecordatorioCaptura tripulanteId={tripulanteId} estado={estado} />}
      {tripulanteId && <RachaMediciones tripulanteId={tripulanteId} estado={estado} />}
    </div>
  );
}
