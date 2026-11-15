import { useTranslation } from "../../../i18n";
import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import Pestanas from "../../../shared/components/Pestanas";
import { useSeccion } from "../../../shared/hooks/useSeccion";
import AnimoDiario from "../components/AnimoDiario";
import DiarioTripulante from "../components/DiarioTripulante";
import Tamizaje from "../components/Tamizaje";
import AvisosCompartidos from "../components/AvisosCompartidos";

const SECCIONES = ["animo", "diario", "apoyo"] as const;
type Seccion = (typeof SECCIONES)[number];

/** Bienestar en pestanas (una seccion a la vez): animo del dia, diario personal y tamizaje con avisos. */
export default function BienestarPage({ tripulanteId }: { tripulanteId: string }) {
  const { t } = useTranslation("bienestar");
  const [seccion, setSeccion] = useSeccion<Seccion>("bienestar", SECCIONES, "animo");
  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta={t(`tabs.${seccion}`)} titulo={t("page.title")} descripcion={t("page.desc")}>
        <span className="chip-estado privado">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
          {t("page.private")}
        </span>
      </EncabezadoPagina>
      <Pestanas
        etiqueta={t("tabs.aria")} valor={seccion} alCambiar={(id) => setSeccion(id as Seccion)}
        pestanas={[{ id: "animo", etiqueta: t("tabs.animo") }, { id: "diario", etiqueta: t("tabs.diario") }, { id: "apoyo", etiqueta: t("tabs.apoyo") }]}
      >
        {seccion === "animo" && <AnimoDiario tripulanteId={tripulanteId} />}
        {seccion === "diario" && <DiarioTripulante tripulanteId={tripulanteId} />}
        {seccion === "apoyo" && (
          <div className="rejilla-ajustes">
            <Tamizaje tripulanteId={tripulanteId} />
            <AvisosCompartidos tripulanteId={tripulanteId} />
          </div>
        )}
      </Pestanas>
    </div>
  );
}
