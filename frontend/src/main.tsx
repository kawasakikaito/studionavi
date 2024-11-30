import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../app/globals.css";
import App_temp from "./App_temp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App_temp />
  </StrictMode>
);
