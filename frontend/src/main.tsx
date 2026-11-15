import "@fontsource-variable/inter";
import "@fontsource-variable/geist-mono";
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import { iniciarPwa } from "./shared/pwa";
import { iniciarRendimiento } from "./shared/rendimiento";
import "./shared/styles/styles.css";

iniciarPwa();
iniciarRendimiento(); // antes del primer pintado: el CSS ligero ya aplica desde el inicio

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
