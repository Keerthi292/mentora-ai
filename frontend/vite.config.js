import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  // BACKEND_URL from frontend/.env. No VITE_ prefix, so it is NOT sent to the browser.
  // Only the dev server (npm run dev) needs it; a production build is served next to the backend.
  const { BACKEND_URL } = loadEnv(mode, process.cwd(), "");
  if (command === "serve" && !BACKEND_URL) {
    throw new Error("BACKEND_URL is missing: add it to frontend/.env (see frontend/.env.example).");
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      // Fail instead of silently switching ports
      strictPort: true,
      // The browser calls /api on this same address and Vite forwards it to the backend,
      // so the login cookie belongs to this site and is sent with every request
      proxy: {
        "/api": { target: BACKEND_URL },
      },
    },
  };
});
