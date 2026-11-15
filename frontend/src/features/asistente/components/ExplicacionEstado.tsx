import { useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import Alerta from "../../../shared/components/Alerta";

interface Explicacion { explicacion: string; fuente: string; generado_por_ia: boolean; nivel_general?: string }

/** Explicacion en lenguaje natural del estado ya calculado (GET /api/estado/{id}/explicacion). Solo explica; el nivel lo deciden las reglas. */
export default function ExplicacionEstado({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  const [datos, setDatos] = useState<Explicacion | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(false);

  async function pedir() {
    setCargando(true); setError(false);
    try { setDatos(await api<Explicacion>(`/estado/${encodeURIComponent(tripulanteId)}/explicacion`)); }
    catch { setError(true); }
    finally { setCargando(false); }
  }

  return (
    <section className="tarjeta pieza">
      <div className="pieza-cab"><div><h2>{t("explica.title")}</h2><p className="suave">{t("explica.hint")}</p></div></div>
      <div className="formulario">
        <div><button type="button" onClick={pedir} disabled={cargando}>{cargando ? t("explica.cargando") : t("explica.boton")}</button></div>
        {error && <Alerta tono="error">{t("explica.error")}</Alerta>}
        {datos && (
          <div aria-live="polite">
            <p className="cuerpo">{datos.explicacion}</p>
            <p className="suave">{datos.generado_por_ia ? t("explica.ia") : t("explica.reglas")}</p>
          </div>
        )}
      </div>
    </section>
  );
}
