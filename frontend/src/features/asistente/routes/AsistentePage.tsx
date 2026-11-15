import { registrarEspanol, useTranslation } from "../../../i18n";
import esAsistente from "../../../i18n/locales/ES/features/asistente/asistente.json";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import ChatAsistente from "../components/ChatAsistente";
import ExplicacionEstado from "../components/ExplicacionEstado";
import PreferenciasAsistente from "../components/PreferenciasAsistente";

registrarEspanol("asistente", esAsistente);

/** Pantalla del asistente: estilo de respuesta, explicacion del estado y como usar la voz. */
export default function AsistentePage({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t("page.kicker")} titulo={t("page.title")} descripcion={t("page.desc")} />
      <div className="bienestar-rejilla">
        <div className="bienestar-col">
          <PreferenciasAsistente tripulanteId={tripulanteId} />
        </div>
        <div className="bienestar-col">
          <ChatAsistente tripulanteId={tripulanteId} />
          <ExplicacionEstado tripulanteId={tripulanteId} />
          <section className="tarjeta pieza">
            <div className="pieza-cab"><div><h2>{t("voz.title")}</h2><p className="suave">{t("voz.hint")}</p></div></div>
            <p className="suave">{t("voz.nota")}</p>
          </section>
        </div>
      </div>
    </div>
  );
}
