import "@fontsource-variable/inter";
import "@fontsource-variable/geist-mono";
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import "./shared/styles/styles.css";
import "./shared/styles/componentes.css";
import "./shared/styles/animaciones.css";
import "./shared/styles/escenario.css";
import "./shared/styles/layout.css";
import "./shared/styles/paginas.css";
import "./shared/styles/alertas.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
