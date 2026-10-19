import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// The project's only .env file is backend/.env
const BACKEND_DIR = fileURLToPath(new URL("../backend", import.meta.url));

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // The backend's address, from API_HOST and API_PORT in backend/.env. Read here in the config
  // only: nothing from backend/.env is sent to the browser. Only the dev server (npm run dev)
  // uses it.
  // Same defaults as backend/app/config.py
  const { API_HOST = "127.0.0.1", API_PORT = "8002" } = loadEnv(mode, BACKEND_DIR, "");
  // 0.0.0.0 means "listen everywhere"; connect to it on this machine
  const host = API_HOST === "0.0.0.0" ? "127.0.0.1" : API_HOST;

  return {
    plugins: [react()],
    server: {
      port: 5173,
      // Fail instead of silently switching ports
      strictPort: true,
      // The browser calls /api on this same address and Vite forwards it to the backend,
      // so the login cookie belongs to this site and is sent with every request
      proxy: {
        "/api": { target: `http://${host}:${API_PORT}` },
      },
    },
  };
});
