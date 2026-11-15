import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";
import Segmentado from "../../../shared/components/Segmentado";

interface Prefs { tono: string; detalle: string; recordatorios: string }
const POR_DEFECTO: Prefs = { tono: "directo", detalle: "completo", recordatorios: "normal" };
const TONOS = ["directo", "calido"];
const DETALLES = ["breve", "completo"];
const RECORDATORIOS = ["minimo", "normal", "frecuente"];

/** Preferencias del asistente (GET/PUT /api/preferencias/{id}); se guardan al elegir y solo las ve su dueño. */
function PreferenciasAsistente({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  const [p, setP] = useState<Prefs>(POR_DEFECTO);
  const opts = (campo: string, vals: string[]) => vals.map((v) => ({ valor: v, etiqueta: t(`prefs.${campo}.${v}`) }));
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);
  useEffect(() => { setMsg(null); api<Prefs>(`/preferencias/${tripulanteId}`).then(setP).catch(() => setP(POR_DEFECTO)); }, [tripulanteId]);

  async function cambiar(campo: keyof Prefs, valor: string) {
    const nuevo = { ...p, [campo]: valor };
    setP(nuevo);
    try {
      setP(await api<Prefs>(`/preferencias/${tripulanteId}`, { method: "PUT", body: JSON.stringify(nuevo) }));
      setMsg({ ok: true, texto: t("prefs.saved") });
    } catch (e) { setMsg({ ok: false, texto: (e as Error).message }); }
  }

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab"><div><h2>{t("prefs.title")}</h2><p className="suave">{t("prefs.hint")}</p></div></div>
      <div className="formulario">
        <div className="campo"><span className="campo-etiqueta">{t("prefs.tone")}</span><Segmentado etiqueta={t("prefs.tone")} opciones={opts("tone", TONOS)} valor={p.tono} alCambiar={(v) => cambiar("tono", v)} /></div>
        <div className="campo"><span className="campo-etiqueta">{t("prefs.detail")}</span><Segmentado etiqueta={t("prefs.detail")} opciones={opts("detail", DETALLES)} valor={p.detalle} alCambiar={(v) => cambiar("detalle", v)} /></div>
        <div className="campo"><span className="campo-etiqueta">{t("prefs.reminders")}</span><Segmentado etiqueta={t("prefs.reminders")} opciones={opts("reminders", RECORDATORIOS)} valor={p.recordatorios} alCambiar={(v) => cambiar("recordatorios", v)} /></div>
        {msg && <Alerta tono={msg.ok ? "ok" : "error"}>{msg.texto}</Alerta>}
      </div>
    </section>
  );
}

export default memo(PreferenciasAsistente);
