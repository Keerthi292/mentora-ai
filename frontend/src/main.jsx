import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

// Bootstrap CSS first, then our own styles so they can override it
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.min.css";
// Bootstrap's JS powers interactive parts like the mobile navbar toggle
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "./index.css";

import App from "./App";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
