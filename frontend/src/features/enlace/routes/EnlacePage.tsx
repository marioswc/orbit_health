import Titular from "../../../shared/components/Titular";
import ConsolaEnlace from "../components/ConsolaEnlace";

export default function EnlacePage() {
  return (
    <div className="col">
      <section className="tarjeta">
        <Titular titulo="Enlace con la Tierra">Qué sale de la nave y en qué orden: primero lo más grave.</Titular>
      </section>
      <ConsolaEnlace />
    </div>
  );
}
