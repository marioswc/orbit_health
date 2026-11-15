import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api, post } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Selector from "../../../shared/components/Selector";
import AvisosMedico from "../components/AvisosMedico";
import ListaAuditoria from "../components/ListaAuditoria";
import Pestanas from "../../../shared/components/Pestanas";
import { useSeccion } from "../../../shared/hooks/useSeccion";
import type { EventoAuditoria, Salud, VerificacionAuditoria } from "../types/sistema";

const SECCIONES = ["estado", "avisos", "auditoria"] as const;
type Seccion = (typeof SECCIONES)[number];

/** Estado del sistema: salud de la base y respaldos, auditoria verificable y reinicio de PIN (medico o comandante). */
export default function SistemaPage() {
  const { t, locale } = useTranslation("sistema");
  const hora = (ts: string) => new Date(ts).toLocaleString(locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const accion = (a: string) => { const k = `audit.action.${a}`; const r = t(k); return r === k ? a.replace(/_/g, " ") : r; };

  const [seccion, setSeccion] = useSeccion<Seccion>("sistema", SECCIONES, "estado");
  const [salud, setSalud] = useState<Salud | null>(null);
  const [errSalud, setErrSalud] = useState("");
  const [eventos, setEventos] = useState<EventoAuditoria[] | null>(null);
  const [errAud, setErrAud] = useState("");
  const [verif, setVerif] = useState<{ ok: boolean; texto: string } | null>(null);
  const [tripulantes, setTripulantes] = useState<{ id: string; nombre: string; rol: string }[]>([]);
  const [objetivoPin, setObjetivoPin] = useState("");
  const [pin, setPin] = useState<{ ok: boolean; texto: string; secreto?: string } | null>(null);

  const nombres = Object.fromEntries(tripulantes.map((x) => [x.id, { nombre: x.nombre, rol: x.rol }]));
  const cargarAuditoria = useCallback(() => {
    api<EventoAuditoria[]>("/auditoria").then((e) => { setEventos(e); setErrAud(""); }).catch((e) => { setEventos([]); setErrAud(e.message); });
  }, []);
  useEffect(() => {
    api<Salud>("/salud").then(setSalud).catch((e) => setErrSalud(e.message));
    api<{ id: string; nombre: string; rol: string }[]>("/tripulantes").then(setTripulantes).catch(() => setTripulantes([]));
    cargarAuditoria();
  }, [cargarAuditoria]);

  async function verificar() {
    try {
      const r = await api<VerificacionAuditoria>("/auditoria/verificar");
      setVerif(r.valida ? { ok: true, texto: t("audit.intact", { total: r.total }) } : { ok: false, texto: t("audit.broken", { id: r.primer_invalido ?? "?" }) });
    } catch (e) { setVerif({ ok: false, texto: (e as Error).message }); }
  }
  async function reiniciar() {
    if (!objetivoPin) return;
    try {
      const r = await post<{ tripulante_id: string; pin_temporal: string }>(`/auth/reiniciar-pin/${objetivoPin}`, {});
      setPin({ ok: true, texto: t("pin.msg", { id: r.tripulante_id }), secreto: r.pin_temporal });
      cargarAuditoria();
    } catch (e) { setPin({ ok: false, texto: (e as Error).message }); }
  }

  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t(`tabs.${seccion}`)} titulo={t("page.title")} descripcion={t("page.desc")}>
        {salud && <span className={`chip-estado ${salud.base_ok ? "activo" : "eclipse"}`}><span className="latido" aria-hidden="true" />{salud.base_ok ? t("chip.ok") : t("chip.bad")}</span>}
      </EncabezadoPagina>

      <Pestanas etiqueta={t("tabs.aria")} valor={seccion} alCambiar={(id) => setSeccion(id as Seccion)}
        pestanas={[{ id: "estado", etiqueta: t("tabs.estado") }, { id: "avisos", etiqueta: t("tabs.avisos") }, { id: "auditoria", etiqueta: t("tabs.auditoria") }]}>
      {seccion === "estado" && (
      <div className="rejilla-2">
        <section className="tarjeta pieza" aria-label={t("health.title")}>
          <h2>{t("health.title")}</h2>
          {errSalud && <Alerta tono="error">{errSalud}</Alerta>}
          {!salud && !errSalud && <span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}
          {salud && (
            <dl className="datos">
              <div><dt>{t("health.db")}</dt><dd>{salud.detalle}</dd></div>
              <div><dt>{t("health.start")}</dt><dd>{salud.arranque?.estado}{salud.arranque?.detalle ? ` · ${salud.arranque.detalle}` : ""}</dd></div>
              <div><dt>{t("health.backups")}</dt><dd>{salud.respaldos}</dd></div>
              <div><dt>{t("health.lastBackup")}</dt><dd>{salud.ultimo_respaldo ?? t("health.none")}</dd></div>
              <div><dt>{t("health.freq")}</dt><dd>{salud.respaldo_cada_min > 0 ? t("health.every", { min: salud.respaldo_cada_min }) : t("health.disabled")}</dd></div>
            </dl>
          )}
        </section>

        <section className="tarjeta pieza" aria-label={t("pin.title")}>
          <h2>{t("pin.title")}</h2>
          <p className="suave">{t("pin.desc")}</p>
          <div className="formulario">
            <div className="campo">
              <span className="campo-etiqueta">{t("pin.crew")}</span>
              <Selector etiqueta={t("pin.crew")} valor={objetivoPin} alCambiar={(v) => { setObjetivoPin(v); setPin(null); }} opciones={tripulantes.map((x) => ({ valor: x.id, etiqueta: `${x.nombre} · ${x.rol}` }))} />
            </div>
            <button type="button" onClick={reiniciar} disabled={!objetivoPin}>{t("pin.button")}</button>
            {pin && <Alerta tono={pin.ok ? "aviso" : "error"} titulo={pin.ok ? t("pin.done") : undefined}>{pin.texto}{pin.secreto && <strong className="pin-temporal">{pin.secreto}</strong>}</Alerta>}
          </div>
        </section>
      </div>
      )}

      {seccion === "avisos" && <AvisosMedico />}

      {seccion === "auditoria" && (
      <section className="tarjeta pieza aud-tabla" aria-label={t("audit.title")}>
        <div className="pieza-cab">
          <div><h2>{t("audit.title")}</h2><p className="suave">{t("audit.desc")}</p></div>
          <button type="button" onClick={verificar}>{t("audit.verify")}</button>
        </div>
        {verif && <Alerta tono={verif.ok ? "ok" : "error"} titulo={verif.ok ? t("audit.okTitle") : t("audit.failTitle")}>{verif.texto}</Alerta>}
        {errAud && <Alerta tono="error" titulo={t("audit.readError")}>{errAud}</Alerta>}
        {eventos === null && <span className="esqueleto" style={{ height: 120 }} aria-busy="true" />}
        {eventos && eventos.length === 0 && !errAud && <p className="vacio">{t("audit.empty")}</p>}
        {eventos && eventos.length > 0 && (
          <ListaAuditoria eventos={eventos} accion={accion} hora={hora} nombres={nombres} />
        )}
      </section>
      )}
      </Pestanas>
    </div>
  );
}
