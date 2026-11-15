import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "../../../i18n";
import { num } from "../../../shared/formato";
import Drawer from "../../../shared/components/Drawer";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Segmentado from "../../../shared/components/Segmentado";
import GraficaSerie from "../../monitor/components/GraficaSerie";
import { useHistorialIndicador } from "../../monitor/hooks/useHistorialIndicador";
import { useSeries } from "../../monitor/hooks/useSeries";
import type { Estado, LecturaEstado, PuntoHistorial } from "../../monitor/types/estado";
import { nombreIndicador } from "../../monitor/utils/indicadores";
import { compararConBase, formatoDelta } from "../../monitor/utils/lineaBase";

const ORDEN: Record<string, number> = { rojo: 0, amarillo: 1, verde: 2 };

/** Minimo, media y maximo de las lecturas reales de los ultimos 14 dias. */
function resumir(puntos?: PuntoHistorial[]) {
  if (!puntos || puntos.length === 0) return null;
  const v = puntos.map((p) => p.valor);
  return { min: Math.min(...v), max: Math.max(...v), media: v.reduce((a, b) => a + b, 0) / v.length, n: v.length };
}

/** Grafica completa de un indicador en un modal (mismo cuadro que el resto de la app). */
function ModalGrafica({ tripulanteId, clave, titulo, alCerrar }: { tripulanteId: string; clave: string | null; titulo: string; alCerrar: () => void }) {
  const hist = useHistorialIndicador(tripulanteId, clave);
  return (
    <Drawer abierto={clave !== null} alCerrar={alCerrar} titulo={titulo}>
      <GraficaSerie serie={hist.serie} cargando={hist.cargando} error={hist.error} alCerrar={alCerrar} compacta />
    </Drawer>
  );
}

/** Historial: tabla de indicadores (actual, minimo, media y maximo de 14 dias, base personal, variacion y estado). */
export default function HistorialPage({ tripulanteId, estado }: { tripulanteId: string; estado: Estado | null }) {
  const { t } = useTranslation("historial");
  const { t: tc } = useTranslation("common");
  const { t: tm, i18n: { language } } = useTranslation("monitor");
  const [filtro, setFiltro] = useState("todos");
  const [grafica, setGrafica] = useState<string | null>(null);
  const cerrar = useCallback(() => setGrafica(null), []);

  const todas = useMemo(
    () => [...(estado?.indicadores ?? [])].sort((a, b) => (ORDEN[a.nivel] ?? 3) - (ORDEN[b.nivel] ?? 3) || nombreIndicador(a.indicador, tm).localeCompare(nombreIndicador(b.indicador, tm), language)),
    [estado, tm, language],
  );
  const filas = useMemo(() => (filtro === "alertas" ? todas.filter((l) => l.nivel !== "verde" || compararConBase(l).desvio) : todas), [todas, filtro]);
  const claves = useMemo(() => todas.slice(0, 12).map((l) => l.indicador), [todas]);
  const series = useSeries(tripulanteId, claves, 200);

  const fila = (l: LecturaEstado) => {
    const c = compararConBase(l);
    const r = resumir(series[l.indicador]);
    const nombre = nombreIndicador(l.indicador, tm);
    return (
      <tr key={l.indicador} className={l.nivel}>
        <th scope="row"><button type="button" className="tabla-enlace" onClick={() => setGrafica(l.indicador)} aria-haspopup="dialog" aria-label={t("row.aria", { nombre, valor: num(l.valor), unidad: l.unidad, nivel: tc(`status.${l.nivel}`), accion: t("row.open") })}>{nombre}</button></th>
        <td className="num"><strong>{num(l.valor)}</strong> <small>{l.unidad}</small></td>
        <td className="num sec">{r ? num(r.min) : "—"}</td>
        <td className="num sec">{r ? num(r.media) : "—"}</td>
        <td className="num sec">{r ? num(r.max) : "—"}</td>
        <td className="num">{c.disponible && c.media !== undefined ? num(c.media) : <span className="suave" title={t("noBase", { n: c.muestras })}>—</span>}</td>
        <td className={`num${c.desvio ? " desvio" : ""}`}>{c.disponible && c.delta !== undefined ? `${c.tendencia} ${formatoDelta(c.delta)}` : <span className="suave">—</span>}</td>
        <td className="estado"><span className={`badge ${l.nivel}`}>{tc(`status.${l.nivel}`)}</span>{c.desvio && <span className="etiqueta-estado desvio">{t("deviation")}</span>}</td>
      </tr>
    );
  };

  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t("page.kicker")} titulo={t("page.title")} descripcion={t("page.desc")}>
        {todas.length > 0 && <span className="chip-estado">{t("count", { count: todas.length })}</span>}
      </EncabezadoPagina>
      {!estado && <span className="esqueleto" style={{ height: 160 }} aria-busy="true" />}
      {estado && todas.length === 0 && <p className="vacio">{t("empty")}</p>}
      {todas.length > 0 && (
        <section className="tarjeta pieza hist-tabla" aria-label={t("aria.list")}>
          <div className="hist-barra">
            <span className="suave hist-ayuda">{t("hint")}</span>
            <Segmentado etiqueta={t("filter.aria")} valor={filtro} alCambiar={setFiltro} opciones={[{ valor: "todos", etiqueta: t("filter.all") }, { valor: "alertas", etiqueta: t("filter.alerts") }]} />
          </div>
          {filas.length === 0 ? <p className="vacio">{t("emptyFilter")}</p> : (
            <div className="tabla-caja">
              <table className="tabla">
                <thead>
                  <tr>
                    <th scope="col">{t("col.indicator")}</th><th scope="col" className="num">{t("col.current")}</th>
                    <th scope="col" className="num sec">{t("col.min")}</th><th scope="col" className="num sec">{t("col.mean")}</th><th scope="col" className="num sec">{t("col.max")}</th>
                    <th scope="col" className="num">{t("col.base")}</th><th scope="col" className="num">{t("col.variation")}</th><th scope="col">{t("col.status")}</th>
                  </tr>
                </thead>
                <tbody>{filas.map(fila)}</tbody>
              </table>
            </div>
          )}
        </section>
      )}
      <ModalGrafica tripulanteId={tripulanteId} clave={grafica} titulo={grafica ? nombreIndicador(grafica, tm) : ""} alCerrar={cerrar} />
    </div>
  );
}
