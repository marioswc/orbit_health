import EncabezadoPagina from "../../../shared/components/EncabezadoPagina";
import AnimoDiario from "../components/AnimoDiario";
import DiarioTripulante from "../components/DiarioTripulante";
import Tamizaje from "../components/Tamizaje";
import AsistentePreferencias from "../components/AsistentePreferencias";

export default function BienestarPage({ tripulanteId }: { tripulanteId: string }) {
  return (
    <div className="pagina">
      <EncabezadoPagina etiqueta="Bienestar" titulo="Bienestar" descripcion="Ánimo, diario y tamizaje privados. Nada de esto se envía a la cola hacia la Tierra.">
        <span className="chip-estado privado">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="9" rx="3" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>
          Privado · solo en este equipo
        </span>
      </EncabezadoPagina>
      <div className="bienestar-rejilla">
        <div className="bienestar-col">
          <AnimoDiario tripulanteId={tripulanteId} />
          <Tamizaje tripulanteId={tripulanteId} />
          <AsistentePreferencias tripulanteId={tripulanteId} />
        </div>
        <DiarioTripulante tripulanteId={tripulanteId} />
      </div>
    </div>
  );
}
