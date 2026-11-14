import DiarioTripulante from "../components/DiarioTripulante";
import Tamizaje from "../components/Tamizaje";

export default function BienestarPage({ tripulanteId }: { tripulanteId: string }) {
  return (
    <div className="grid">
      <DiarioTripulante tripulanteId={tripulanteId} />
      <Tamizaje tripulanteId={tripulanteId} />
    </div>
  );
}
