import { useEffect, useRef, useState, type ReactNode } from "react";
import Contador from "../../../shared/components/Contador";
import Titular from "../../../shared/components/Titular";
import DetalleZona from "../components/DetalleZona";
import FiguraHumana from "../components/FiguraHumana";
import TarjetaSignoVital from "../components/TarjetaSignoVital";
import { useZonaSeleccionada } from "../hooks/useZonaSeleccionada";
import type { Estado, LecturaEstado } from "../types/estado";
import { CAPAS, ZONAS, nivelZona, type NivelZona } from "../zonas";

interface Props {
  estado: Estado | null;
  /** Espacio para acciones de otras features (p. ej. captura de mediciones), compuesto desde app/. */
  children?: ReactNode;
  /** Monitor de cabina (feature cabina), compuesto desde app/: se muestra en la columna izquierda. */
  cabina?: ReactNode;
  /** Peor nivel del aire/radiacion de cabina, para marcar Cabeza y Respiratorio en la figura. */
  ambiente?: NivelZona | null;
}

const SIN_LECTURAS: LecturaEstado[] = []; // referencia estable: evita recalcular niveles en cada render
const TITULAR = { verde: "Sin alertas activas", amarillo: "Requiere vigilancia", rojo: "Atención inmediata", sin_datos: "Sin lecturas recientes" } as const;
const LEYENDA: [string, string][] = [["verde", "Verde"], ["amarillo", "Amarillo"], ["rojo", "Rojo"], ["sin_datos", "Sin datos"]];

export default function MonitorPage({ estado, children, cabina, ambiente = null }: Props) {
  const { zona, acercado, capa, setCapa, elegir, alejar } = useZonaSeleccionada();
  const [meses, setMeses] = useState(0);
  const nivel = estado?.nivel_general ?? "sin_datos";
  const lecturas = estado?.indicadores ?? SIN_LECTURAS;

  // Tras la primera carga, las filas cuyo valor cambia destellan (la clave incluye valor y hora)
  const cargado = useRef(false);
  const destellar = cargado.current;
  useEffect(() => { if (estado) cargado.current = true; }, [estado]);

  return (
    <div className="vista">
      <div className="titulo-pagina">
        {estado ? (
          <>
            <Titular key={nivel} titulo={TITULAR[nivel]}>
              NEWS2: <Contador valor={estado.news2.puntos} /> puntos en una ventana de {estado.ventana_min} min.
            </Titular>
            <p style={{ marginTop: 16 }}>
              <span className={`badge ${nivel}`}>{nivel === "sin_datos" ? "sin datos" : nivel}</span>
            </p>
            {estado.news2.faltantes.length > 0 && (
              <p className="suave">Variables NEWS2 sin dato reciente: {estado.news2.faltantes.join(", ")}. El puntaje puede estar subestimado.</p>
            )}
          </>
        ) : (
          <div aria-busy="true" aria-label="Cargando estado">
            <span className="esqueleto" style={{ width: "min(420px, 80%)", height: 52 }} />
            <span className="esqueleto" style={{ width: 260, height: 18, marginTop: 16 }} />
          </div>
        )}
      </div>

      <section className="escenario" aria-label="Estado por zona del cuerpo">
        <aside className="lado izq">
          <div className="panel">
            <h2>Zonas</h2>
            <div className="zonas-lista" role="group" aria-label="Zonas del cuerpo">
              {ZONAS.map((z) => (
                <button key={z.id} type="button" className={`tab ${nivelZona(z.indicadores, lecturas)} ${zona === z.id ? "activo" : ""}`} aria-pressed={zona === z.id} onClick={() => elegir(z.id)}>
                  {z.etiqueta}
                </button>
              ))}
            </div>
          </div>
          <div className="panel">
            <h2>Capas</h2>
            <div className="capas" role="group" aria-label="Capa del cuerpo a mostrar">
              {CAPAS.map((c) => (
                <button key={c.id} type="button" className={capa === c.id ? "activo" : ""} aria-pressed={capa === c.id} onClick={() => setCapa(c.id)}>{c.etiqueta}</button>
              ))}
            </div>
          </div>
          <div className="panel">
            <h2>Estados</h2>
            <ul className="leyenda" aria-label="Leyenda de estados">
              {LEYENDA.map(([k, t]) => <li key={k}><span className={`badge ${k}`}>{t}</span></li>)}
            </ul>
          </div>
          {cabina}
        </aside>

        <div className="centro">
          <FiguraHumana lecturas={lecturas} seleccionada={zona} acercado={acercado} capa={capa} meses={meses} alSeleccionar={elegir} alAlejar={alejar} ambiente={ambiente} />
        </div>

        <aside className="lado der">
          <DetalleZona id={zona} lecturas={lecturas} capa={capa} meses={meses} alMeses={setMeses} />
        </aside>
      </section>

      <div className="fila-2">
        {children}
        {lecturas.length > 0 && (
          <section className="tarjeta">
            <h2>Indicadores</h2>
            <div className="signos">
              {lecturas.map((i) => <TarjetaSignoVital key={`${i.indicador}-${i.valor}-${i.ts}`} lectura={i} destello={destellar} />)}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
