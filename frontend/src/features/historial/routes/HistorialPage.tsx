import { useEffect, useMemo, useState } from "react";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import GraficaSerie from "../../monitor/components/GraficaSerie";
import { useHistorialIndicador } from "../../monitor/hooks/useHistorialIndicador";
import type { Estado, LecturaEstado } from "../../monitor/types/estado";
import { nombreIndicador } from "../../monitor/utils/indicadores";
import { compararConBase, formatoDelta } from "../../monitor/utils/lineaBase";

const ORDEN: Record<string, number> = { rojo: 0, amarillo: 1, verde: 2 };

function Fila({ l, tripulanteId, abierta, alAlternar }: { l: LecturaEstado; tripulanteId: string; abierta: boolean; alAlternar: () => void }) {
  const c = compararConBase(l);
  // El contenido sigue montado mientras el cajon se cierra, para que la salida tambien se anime
  const [montado, setMontado] = useState(false);
  useEffect(() => {
    if (abierta) { setMontado(true); return; }
    const t = window.setTimeout(() => setMontado(false), 400);
    return () => window.clearTimeout(t);
  }, [abierta]);
  const hist = useHistorialIndicador(tripulanteId, abierta || montado ? l.indicador : null);
  const nombre = nombreIndicador(l.indicador);
  return (
    <li className={`hist-fila ${l.nivel}${abierta ? " abierta" : ""}`}>
      <button type="button" className="hist-cab" onClick={alAlternar} aria-expanded={abierta} aria-label={`${nombre}: ${l.valor} ${l.unidad}, ${l.nivel}. ${abierta ? "Ocultar" : "Ver"} gráfica`}>
        <span className="hist-nombre">{nombre}</span>
        <span className="hist-valor">{l.valor} <small>{l.unidad}</small></span>
        <span className="hist-base">
          {c.disponible && c.media !== undefined && c.delta !== undefined
            ? <>Base 14 d: {Number(c.media.toFixed(1))} {l.unidad} <em>({formatoDelta(c.delta)})</em></>
            : <span className="suave">Sin base suficiente ({c.muestras})</span>}
        </span>
        <span className="hist-estado">
          <span className="tendencia" aria-hidden="true">{c.tendencia}</span>
          {c.desvio && <span className="etiqueta-estado desvio">Desvío &gt; 2σ</span>}
          <span className={`badge ${l.nivel}`}>{l.nivel}</span>
        </span>
        <span className="hist-flecha" aria-hidden="true" />
      </button>
      <div className="hist-despliegue" aria-hidden={!abierta}>
        <div className="hist-grafica">
          {(abierta || montado) && <GraficaSerie serie={hist.serie} cargando={hist.cargando} error={hist.error} alCerrar={alAlternar} />}
        </div>
      </div>
    </li>
  );
}

/** Historial: cada indicador en una fila (valor actual, linea base personal y estado) que despliega su grafica. */
export default function HistorialPage({ tripulanteId, estado }: { tripulanteId: string; estado: Estado | null }) {
  const [abierto, setAbierto] = useState<string | null>(null);
  const filas = useMemo(
    () => [...(estado?.indicadores ?? [])].sort((a, b) => (ORDEN[a.nivel] ?? 3) - (ORDEN[b.nivel] ?? 3) || nombreIndicador(a.indicador).localeCompare(nombreIndicador(b.indicador), "es")),
    [estado],
  );
  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta="Historial" titulo="Tus indicadores en el tiempo" descripcion="Cada valor frente a tu propia línea base de 14 días. Abre una fila para ver su gráfica.">
        {filas.length > 0 && <span className="chip-estado">{filas.length} {filas.length === 1 ? "indicador" : "indicadores"}</span>}
      </EncabezadoPagina>
      {!estado && <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      {estado && filas.length === 0 && <p className="vacio">Aún no hay lecturas. Registra una con "Captura manual".</p>}
      {filas.length > 0 && (
        <section className="tarjeta pieza" aria-label="Indicadores">
          <ul className="hist-lista">
            {filas.map((l) => (
              <Fila key={l.indicador} l={l} tripulanteId={tripulanteId} abierta={abierto === l.indicador} alAlternar={() => setAbierto((a) => (a === l.indicador ? null : l.indicador))} />
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
