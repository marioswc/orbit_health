import FiguraHumana from "./components/FiguraHumana";
import PanelMedicion from "./components/PanelMedicion";
import DiarioTripulante from "./components/DiarioTripulante";
import ConsolaEnlace from "./components/ConsolaEnlace";

export default function App() {
  return (
    <main>
      <h1>ORBIT Health</h1>
      <FiguraHumana />
      <PanelMedicion />
      <DiarioTripulante />
      <ConsolaEnlace />
    </main>
  );
}
