import Titular from "../../../shared/components/Titular";
import DiarioTripulante from "../components/DiarioTripulante";
import Tamizaje from "../components/Tamizaje";

export default function BienestarPage({ tripulanteId }: { tripulanteId: string }) {
  return (
    <div className="col">
      <section className="tarjeta">
        <Titular titulo="Bienestar">Diario y tamizaje de ánimo privados. Nada de esto se envía a la cola hacia la Tierra.</Titular>
      </section>
      <div className="col" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", alignItems: "start" }}>
        <DiarioTripulante tripulanteId={tripulanteId} />
        <Tamizaje tripulanteId={tripulanteId} />
      </div>
    </div>
  );
}
