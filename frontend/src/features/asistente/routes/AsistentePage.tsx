import { registrarEspanol, useTranslation } from "../../../i18n";
import esAsistente from "../../../i18n/locales/ES/features/asistente/asistente.json";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Pestanas from "../../../shared/components/Pestanas";
import { useSeccion } from "../../../shared/hooks/useSeccion";
import ChatAsistente from "../components/ChatAsistente";
import ExplicacionEstado from "../components/ExplicacionEstado";
import PerfilNova from "../components/PerfilNova";
import PreferenciasAsistente from "../components/PreferenciasAsistente";

registrarEspanol("asistente", esAsistente);

const SECCIONES = ["chat", "ajustes", "estado"] as const;
type Seccion = (typeof SECCIONES)[number];

/** Pantalla del asistente en pestanas: chat con Nova, ajustes (estilo, perfil y voz) y explicacion del estado. */
export default function AsistentePage({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("asistente");
  const [seccion, setSeccion] = useSeccion<Seccion>("asistente", SECCIONES, "chat");
  return (
    <div className={`pagina${seccion === "chat" ? " pagina-chat" : ""}`}>
      {seccion !== "chat" && <EncabezadoPagina etiqueta={t(`tabs.${seccion}`)} titulo={t("page.title")} descripcion={t("page.desc")} />}
      <Pestanas
        etiqueta={t("tabs.aria")} valor={seccion} alCambiar={(id) => setSeccion(id as Seccion)}
        pestanas={[{ id: "chat", etiqueta: t("tabs.chat") }, { id: "ajustes", etiqueta: t("tabs.ajustes") }, { id: "estado", etiqueta: t("tabs.estado") }]}
      >
        {seccion === "chat" && <ChatAsistente tripulanteId={tripulanteId} />}
        {seccion === "ajustes" && (
          <div className="rejilla-ajustes">
            <PreferenciasAsistente tripulanteId={tripulanteId} />
            <PerfilNova tripulanteId={tripulanteId} />
            <section className="tarjeta pieza">
              <div className="pieza-cab"><div><h2>{t("voz.title")}</h2><p className="suave">{t("voz.hint")}</p></div></div>
              <p className="suave">{t("voz.nota")}</p>
            </section>
          </div>
        )}
        {seccion === "estado" && <div className="ancho-lectura"><ExplicacionEstado tripulanteId={tripulanteId} /></div>}
      </Pestanas>
    </div>
  );
}
