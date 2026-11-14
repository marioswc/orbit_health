import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "../../../i18n";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import GraficaSerie from "../../monitor/components/GraficaSerie";
import { useHistorialIndicador } from "../../monitor/hooks/useHistorialIndicador";
import type { Estado, LecturaEstado } from "../../monitor/types/estado";
import { nombreIndicador } from "../../monitor/utils/indicadores";
import { compararConBase, formatoDelta } from "../../monitor/utils/lineaBase";

const ORDEN: Record<string, number> = { rojo: 0, amarillo: 1, verde: 2 };

function Fila({ l, tripulanteId, abierta, alAlternar }: { l: LecturaEstado; tripulanteId: string; abierta: boolean; alAlternar: () => void }) {
  const { t } = useTranslation("historial");
  const { t: tc } = useTranslation("common");
  const { t: tm } = useTranslation("monitor");
  const c = compararConBase(l);
  // El contenido sigue montado mientras el cajon se cierra, para que la salida tambien se anime
  const [montado, setMontado] = useState(false);
  useEffect(() => {
    if (abierta) { setMontado(true); return; }
    const id = window.setTimeout(() => setMontado(false), 400);
    return () => window.clearTimeout(id);
  }, [abierta]);
  const hist = useHistorialIndicador(tripulanteId, abierta || montado ? l.indicador : null);
  const nombre = nombreIndicador(l.indicador, tm);
  const nivel = tc(`status.${l.nivel}`);
  return (
    <li className={`hist-fila ${l.nivel}${abierta ? " abierta" : ""}`}>
      <button type="button" className="hist-cab" onClick={alAlternar} aria-expanded={abierta}
        aria-label={t("row.aria", { nombre, valor: l.valor, unidad: l.unidad, nivel, accion: abierta ? t("row.close") : t("row.open") })}>
        <span className="hist-nombre">{nombre}</span>
        <span className="hist-valor">{l.valor} <small>{l.unidad}</small></span>
        <span className="hist-base">
          {c.disponible && c.media !== undefined && c.delta !== undefined
            ? <>{t("base", { media: Number(c.media.toFixed(1)), unidad: l.unidad })} <em>({formatoDelta(c.delta)})</em></>
            : <span className="suave">{t("noBase", { n: c.muestras })}</span>}
        </span>
        <span className="hist-estado">
          <span className="tendencia" aria-hidden="true">{c.tendencia}</span>
          {c.desvio && <span className="etiqueta-estado desvio">{t("deviation")}</span>}
          <span className={`badge ${l.nivel}`}>{nivel}</span>
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
  const { t } = useTranslation("historial");
  const { t: tm, i18n: { language } } = useTranslation("monitor");
  const [abierto, setAbierto] = useState<string | null>(null);
  const filas = useMemo(
    () => [...(estado?.indicadores ?? [])].sort((a, b) => (ORDEN[a.nivel] ?? 3) - (ORDEN[b.nivel] ?? 3) || nombreIndicador(a.indicador, tm).localeCompare(nombreIndicador(b.indicador, tm), language)),
    [estado, tm, language],
  );
  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t("page.kicker")} titulo={t("page.title")} descripcion={t("page.desc")}>
        {filas.length > 0 && <span className="chip-estado">{t("count", { count: filas.length })}</span>}
      </EncabezadoPagina>
      {!estado && <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      {estado && filas.length === 0 && <p className="vacio">{t("empty")}</p>}
      {filas.length > 0 && (
        <section className="tarjeta pieza" aria-label={t("aria.list")}>
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
