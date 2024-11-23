import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App_temp from "./App_temp";
import "./output.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App_temp />
  </StrictMode>
);
