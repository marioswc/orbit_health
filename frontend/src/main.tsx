import "@fontsource-variable/inter";
import "@fontsource-variable/geist-mono";
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import { iniciarRendimiento } from "./shared/rendimiento";
import "./shared/styles/styles.css";
import "./shared/styles/componentes.css";
import "./shared/styles/animaciones.css";
import "./shared/styles/escenario.css";
import "./shared/styles/layout.css";
import "./shared/styles/paginas.css";
import "./shared/styles/alertas.css";
import "./shared/styles/bienestar.css";
import "./shared/styles/conocimiento.css";
import "./shared/styles/complementos.css";
import "./shared/styles/consola.css";
import "./shared/styles/banda.css";
import "./shared/styles/ligero.css";

// PWA: solo en producción y en un contexto seguro (localhost o HTTPS); en la red de la cabina por HTTP simple no aplica.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => { navigator.serviceWorker.register("/sw.js").catch(() => undefined); });
}

iniciarRendimiento(); // antes del primer pintado: el CSS ligero ya aplica desde el inicio

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
