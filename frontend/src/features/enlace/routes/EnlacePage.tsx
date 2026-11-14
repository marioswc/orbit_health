import ConsolaEnlace from "../components/ConsolaEnlace";
import SimuladorDemo from "../components/SimuladorDemo";
import VistaTierra from "../components/VistaTierra";

export default function EnlacePage() {
  return (
    <div className="pagina">
      <ConsolaEnlace />
      <VistaTierra />
      <SimuladorDemo />
    </div>
  );
}
